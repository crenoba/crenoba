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
    risk_level: str
    reason: str


class PermissionManager:
    """Central policy for deciding whether a registered tool may run."""

    READ_ONLY_TOOLS = frozenset(
        {
            "list_files",
            "read_text_file",
            "git_status",
            "git_diff_stat",
            "git_diff_names",
            "git_diff",
            "python_version",
            "pip_version",
            "python_compile_file",
            "python_compile_all",
            "run_pytest",
        }
    )

    APPROVAL_TOOLS = frozenset(
        {
            "write_text_file",
            "git_add",
            "git_commit",
        }
    )

    BLOCKED_TOOLS = frozenset(
        {
            "git_push",
            "git_reset",
            "delete_file",
            "run_arbitrary_shell",
        }
    )

    def evaluate(self, tool_name: str, approved: bool = False) -> PermissionDecision:
        if tool_name in self.BLOCKED_TOOLS:
            return PermissionDecision(
                allowed=False,
                risk_level=RiskLevel.BLOCKED.value,
                reason="이 도구는 현재 안전 정책에 따라 차단되어 있습니다.",
            )

        if tool_name in self.READ_ONLY_TOOLS:
            return PermissionDecision(
                allowed=True,
                risk_level=RiskLevel.READ_ONLY.value,
                reason="안전한 조회 또는 검사 도구입니다.",
            )

        if tool_name in self.APPROVAL_TOOLS:
            if not approved:
                return PermissionDecision(
                    allowed=False,
                    risk_level=RiskLevel.APPROVAL_REQUIRED.value,
                    reason="이 작업은 사용자 승인 후에만 실행할 수 있습니다.",
                )
            return PermissionDecision(
                allowed=True,
                risk_level=RiskLevel.APPROVAL_REQUIRED.value,
                reason="사용자 승인이 확인되었습니다.",
            )

        return PermissionDecision(
            allowed=False,
            risk_level=RiskLevel.BLOCKED.value,
            reason=f"권한 정책에 등록되지 않은 도구입니다: {tool_name}",
        )
