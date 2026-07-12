from __future__ import annotations

from typing import Any

from core.tool_router import ToolRouter


class ComputerAgent:
    """Phase-1 deterministic agent for safe project inspection."""

    def __init__(self, tool_router: ToolRouter) -> None:
        self.tool_router = tool_router

    def inspect_project(self, cwd: str = ".") -> dict[str, Any]:
        plan = [
            "프로젝트 파일 목록 확인",
            "Git 브랜치와 변경 파일 확인",
            "변경 파일 통계 확인",
            "변경된 파일 이름 확인",
        ]

        steps = [
            self.tool_router.execute(
                "list_files",
                {"path": cwd, "recursive": False, "max_results": 100},
            ),
            self.tool_router.execute("git_status", {"cwd": cwd}),
            self.tool_router.execute("git_diff_stat", {"cwd": cwd}),
            self.tool_router.execute("git_diff_names", {"cwd": cwd}),
        ]

        return {
            "success": all(step.get("success", False) for step in steps),
            "mode": "computer",
            "agent": "computer_inspector",
            "plan": plan,
            "steps": steps,
        }
