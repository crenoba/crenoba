from __future__ import annotations

from time import perf_counter
from typing import Any

from core.action_logger import ActionLogger
from core.approval_store import ApprovalStore
from core.tool_router import ToolRouter
from tools.file_tools import preview_write_text_file
from tools.git_tools import preview_git_add, preview_git_commit


class ApprovalService:
    """Prepare previews and execute one-time approved actions."""

    def __init__(
        self,
        tool_router: ToolRouter,
        approval_store: ApprovalStore,
        logger: ActionLogger,
    ) -> None:
        self.tool_router = tool_router
        self.approval_store = approval_store
        self.logger = logger

    def prepare(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        started = perf_counter()
        try:
            preview = self._build_preview(tool, arguments)
            safe_arguments = dict(arguments)

            if tool == "write_text_file":
                safe_arguments["expected_before_sha256"] = preview.get("before_sha256")
            elif tool == "git_add":
                safe_arguments["expected_status_sha256"] = preview.get("status_sha256")
            elif tool == "git_commit":
                safe_arguments["expected_staged_sha256"] = preview.get("staged_sha256")

            pending = self.approval_store.create(
                tool=tool,
                arguments=safe_arguments,
                preview=preview,
            )
            elapsed = round(perf_counter() - started, 3)
            response = {
                "success": True,
                "status": "approval_required",
                "requires_approval": True,
                "action_id": pending.action_id,
                "tool": tool,
                "preview": preview,
                "expires_at": pending.expires_at,
                "elapsed_sec": elapsed,
            }
            self.logger.write(
                {
                    "event": "approval_requested",
                    "tool": tool,
                    "action_id": pending.action_id,
                    "preview_summary": self._preview_summary(preview),
                }
            )
            return response
        except Exception as exc:
            return {
                "success": False,
                "status": "preview_failed",
                "requires_approval": False,
                "tool": tool,
                "message": str(exc),
                "elapsed_sec": round(perf_counter() - started, 3),
            }

    def approve(self, action_id: str) -> dict[str, Any]:
        pending = self.approval_store.consume(action_id)
        if pending is None:
            return {
                "success": False,
                "status": "invalid_or_expired",
                "requires_approval": False,
                "message": "승인 요청을 찾을 수 없거나 이미 사용·취소·만료되었습니다.",
            }

        self.logger.write(
            {
                "event": "approval_granted",
                "tool": pending.tool,
                "action_id": action_id,
            }
        )
        result = self.tool_router.execute(
            tool_name=pending.tool,
            arguments=pending.arguments,
            approved=True,
        )
        return {
            **result,
            "status": "executed" if result.get("success") else "execution_failed",
            "action_id": action_id,
            "requires_approval": False,
        }

    def cancel(self, action_id: str) -> dict[str, Any]:
        pending = self.approval_store.cancel(action_id)
        if pending is None:
            return {
                "success": False,
                "status": "invalid_or_expired",
                "requires_approval": False,
                "message": "취소할 승인 요청을 찾을 수 없습니다.",
            }

        self.logger.write(
            {
                "event": "approval_cancelled",
                "tool": pending.tool,
                "action_id": action_id,
            }
        )
        return {
            "success": True,
            "status": "cancelled",
            "requires_approval": False,
            "tool": pending.tool,
            "action_id": action_id,
            "message": "작업을 취소했습니다. 컴퓨터에는 변경 사항이 적용되지 않았습니다.",
        }

    def _build_preview(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        root = self.tool_router.workspace_root
        if tool == "write_text_file":
            return preview_write_text_file(workspace_root=root, **arguments)
        if tool == "git_add":
            return preview_git_add(workspace_root=root, **arguments)
        if tool == "git_commit":
            return preview_git_commit(workspace_root=root, **arguments)
        raise ValueError(f"승인 미리보기를 지원하지 않는 도구입니다: {tool}")

    @staticmethod
    def _preview_summary(preview: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in preview.items()
            if key not in {"diff", "content", "stdout", "stderr"}
        }
