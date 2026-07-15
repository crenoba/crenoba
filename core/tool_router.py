from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any

from core.action_logger import ActionLogger
from core.permission_manager import PermissionManager
from tools.tool_registry import execute_registered_tool, list_registered_tools


class ToolRouter:
    def __init__(self, workspace_root: Path, log_file: Path) -> None:
        self.workspace_root = workspace_root.resolve()
        self.permission_manager = PermissionManager()
        self.logger = ActionLogger(log_file)

    def tools(self) -> list[dict[str, str]]:
        return list_registered_tools()

    def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        approved: bool = False,
    ) -> dict[str, Any]:
        decision = self.permission_manager.evaluate(tool_name, approved=approved)

        if not decision.allowed:
            response = {
                "success": False,
                "tool": tool_name,
                "risk_level": decision.risk_level,
                "requires_approval": decision.risk_level == "approval_required",
                "message": decision.reason,
                "result": None,
            }
            self.logger.write({"event": "tool_denied", **response})
            return response

        started = perf_counter()
        try:
            result = execute_registered_tool(
                tool_name=tool_name,
                workspace_root=self.workspace_root,
                arguments=arguments,
            )
            elapsed = round(perf_counter() - started, 3)
            tool_success = bool(result.get("success", True))
            response = {
                "success": tool_success,
                "tool": tool_name,
                "risk_level": decision.risk_level,
                "requires_approval": False,
                "message": (
                    "도구 실행이 완료되었습니다."
                    if tool_success
                    else result.get("stderr")
                    or result.get("stdout")
                    or "도구 실행에 실패했습니다."
                ),
                "elapsed_sec": elapsed,
                "result": result,
            }
            self.logger.write(
                {"event": "tool_executed" if tool_success else "tool_failed", **response}
            )
            return response
        except Exception as exc:
            elapsed = round(perf_counter() - started, 3)
            response = {
                "success": False,
                "tool": tool_name,
                "risk_level": decision.risk_level,
                "requires_approval": False,
                "message": str(exc),
                "elapsed_sec": elapsed,
                "result": None,
            }
            self.logger.write({"event": "tool_failed", **response})
            return response
