from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RiskLevel(StrEnum):
    READ_ONLY = "read_only"
    APPROVAL_REQUIRED = "approval_required"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    risk_level: RiskLevel
    reason: str


class PermissionManager:
    """Central policy for deciding whether a registered tool may run."""

    READ_ONLY_TOOLS = {
        "list_files",
        "read_text_file",
        "git_status",
        "git_diff_stat",
        "git_diff_names",
        "git_diff",
        "python_version",
        "pip_version",
    }

    APPROVAL_TOOLS = {
        "write_text_file",
        "git_add",
        "git_commit",
    }

    BLOCKED_TOOLS = {
        "delete_file",
        "git_push",
        "git_reset",
        "run_arbitrary_shell",
    }

    def evaluate(self, tool_name: str, approved: bool = False) -> PermissionDecision:
        if tool_name in self.READ_ONLY_TOOLS:
            return PermissionDecision(
                allowed=True,
                risk_level=RiskLevel.READ_ONLY,
                reason="조회 전용 도구이므로 자동 실행할 수 있습니다.",
            )

        if tool_name in self.APPROVAL_TOOLS:
            if approved:
                return PermissionDecision(
                    allowed=True,
                    risk_level=RiskLevel.APPROVAL_REQUIRED,
                    reason="일회성 사용자 승인이 확인되었습니다.",
                )
            return PermissionDecision(
                allowed=False,
                risk_level=RiskLevel.APPROVAL_REQUIRED,
                reason="컴퓨터 상태를 변경하는 작업이므로 미리보기와 사용자 승인이 필요합니다.",
            )

        if tool_name in self.BLOCKED_TOOLS:
            return PermissionDecision(
                allowed=False,
                risk_level=RiskLevel.BLOCKED,
                reason="현재 버전에서 위험 작업으로 차단되어 있습니다.",
            )

        return PermissionDecision(
            allowed=False,
            risk_level=RiskLevel.BLOCKED,
            reason="등록되지 않은 도구입니다.",
        )
