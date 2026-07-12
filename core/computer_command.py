from __future__ import annotations

import re
from time import perf_counter
from typing import Any

from core.agent_loop import ComputerAgent
from core.tool_router import ToolRouter


COMPUTER_PREFIXES = ("/crenoba computer", "/computer")
TEXT_FILE_PATTERN = re.compile(
    r"(?P<path>(?:[\w가-힣@()\[\]{}+,. -]+[\\/])*"
    r"[\w가-힣@()\[\]{}+,. -]+\."
    r"(?:py|js|ts|html|css|json|md|txt|yaml|yml|toml|ini|cfg|env|log|csv|xml))",
    re.IGNORECASE,
)
QUOTED_PATH_PATTERN = re.compile(r"[\"'`](.+?)[\"'`]")


class ComputerCommandAgent:
    """Route natural-language computer commands to safe, registered tools."""

    def __init__(self, tool_router: ToolRouter) -> None:
        self.tool_router = tool_router
        self.inspector = ComputerAgent(tool_router)

    def run(self, prompt: str, cwd: str = ".") -> dict[str, Any]:
        started = perf_counter()
        request = self._strip_prefix(prompt)
        action, arguments = self._select_action(request=request, cwd=cwd)

        if action == "inspect_project":
            raw_result = self.inspector.inspect_project(cwd=cwd)
            success = raw_result.get("success", False)
        else:
            raw_result = self.tool_router.execute(action, arguments)
            success = raw_result.get("success", False)

        elapsed = round(perf_counter() - started, 2)
        return {
            "success": success,
            "output": self._format_output(action, request, raw_result),
            "mode": "computer",
            "agent": self._agent_name(action),
            "provider": "local-tools",
            "model": "safe-rule-router",
            "response_time_sec": elapsed,
            "selected_tool": action,
            "arguments": arguments,
            "raw_result": raw_result,
        }

    @staticmethod
    def _strip_prefix(prompt: str) -> str:
        text = (prompt or "").strip()
        lowered = text.lower()
        for prefix in COMPUTER_PREFIXES:
            if lowered.startswith(prefix):
                return text[len(prefix) :].strip()
        return text

    def _select_action(self, request: str, cwd: str) -> tuple[str, dict[str, Any]]:
        text = request.lower().strip()
        path = self._extract_path(request)

        if not text:
            return "inspect_project", {"cwd": cwd}

        if ("pip" in text and "버전" in text) or "pip version" in text:
            return "pip_version", {}

        if any(keyword in text for keyword in ("파이썬 버전", "python 버전", "python version")):
            return "python_version", {}

        read_keywords = ("읽어", "내용 보여", "내용 확인", "파일 내용", "열어줘", "열어 줘")
        if path and any(keyword in text for keyword in read_keywords):
            return "read_text_file", {"path": path}

        if any(keyword in text for keyword in ("diff", "수정 내용", "변경 내용", "코드 차이", "차이점")):
            arguments: dict[str, Any] = {"cwd": cwd}
            if path:
                arguments["path"] = path
            return "git_diff", arguments

        if any(keyword in text for keyword in ("변경 파일", "수정된 파일", "파일 이름", "name-status")):
            return "git_diff_names", {"cwd": cwd}

        if any(keyword in text for keyword in ("변경 통계", "수정 통계", "diff stat", "통계")):
            return "git_diff_stat", {"cwd": cwd}

        if any(keyword in text for keyword in ("git 상태", "깃 상태", "git status", "브랜치 상태", "현재 브랜치")):
            return "git_status", {"cwd": cwd}

        if any(keyword in text for keyword in ("파일 목록", "폴더 목록", "프로젝트 구조", "디렉터리", "폴더 구조")):
            return "list_files", {
                "path": path or cwd,
                "recursive": "전체" in text or "하위" in text,
                "max_results": 200,
            }

        # Ambiguous inspection requests intentionally use the safe read-only bundle.
        return "inspect_project", {"cwd": cwd}

    @staticmethod
    def _extract_path(request: str) -> str | None:
        quoted = QUOTED_PATH_PATTERN.search(request)
        if quoted:
            return quoted.group(1).strip()

        file_match = TEXT_FILE_PATTERN.search(request)
        if file_match:
            return file_match.group("path").strip()

        return None

    @staticmethod
    def _agent_name(action: str) -> str:
        names = {
            "inspect_project": "computer_inspector",
            "list_files": "file_inspector",
            "read_text_file": "file_reader",
            "git_status": "git_inspector",
            "git_diff_stat": "git_inspector",
            "git_diff_names": "git_inspector",
            "git_diff": "git_inspector",
            "python_version": "system_inspector",
            "pip_version": "system_inspector",
        }
        return names.get(action, "computer_agent")

    def _format_output(
        self,
        action: str,
        request: str,
        payload: dict[str, Any],
    ) -> str:
        title = "[CRENOBA Computer Agent]"
        request_text = request or "현재 프로젝트 전체 점검"

        if action == "inspect_project":
            return self._format_inspection(title, request_text, payload)

        if not payload.get("success", False):
            message = payload.get("message", "도구 실행에 실패했습니다.")
            return "\n".join(
                [
                    title,
                    f"요청: {request_text}",
                    f"선택 도구: {action}",
                    "상태: 실패",
                    "",
                    str(message),
                ]
            )

        result = payload.get("result") or {}
        formatted = self._format_tool_result(action, result)
        return "\n".join(
            [
                title,
                f"요청: {request_text}",
                f"선택 도구: {action}",
                "권한: 조회 전용 자동 실행",
                "상태: 완료",
                "",
                formatted,
            ]
        )

    def _format_inspection(
        self,
        title: str,
        request_text: str,
        payload: dict[str, Any],
    ) -> str:
        lines = [
            title,
            f"요청: {request_text}",
            "선택 작업: 프로젝트 안전 점검",
            "권한: 조회 전용 자동 실행",
            f"상태: {'완료' if payload.get('success') else '일부 실패'}",
            "",
        ]

        labels = ["프로젝트 파일", "Git 상태", "변경 통계", "변경 파일"]
        for index, step in enumerate(payload.get("steps", []), start=1):
            label = labels[index - 1] if index <= len(labels) else f"단계 {index}"
            lines.append(f"{index}. {label}")
            if step.get("success"):
                result = step.get("result") or {}
                lines.append(self._format_tool_result(step.get("tool", ""), result))
            else:
                lines.append(f"실패: {step.get('message', '알 수 없는 오류')}")
            lines.append("")

        return "\n".join(lines).rstrip()

    @staticmethod
    def _format_tool_result(action: str, result: dict[str, Any]) -> str:
        if action == "list_files":
            items = result.get("items", [])
            lines = [
                f"경로: {result.get('requested_path', '.')}",
                f"항목 수: {result.get('count', len(items))}",
            ]
            for item in items:
                marker = "[DIR]" if item.get("type") == "directory" else "[FILE]"
                lines.append(f"{marker} {item.get('path', '')}")
            if result.get("truncated"):
                lines.append("... 결과가 많아 일부만 표시했습니다.")
            return "\n".join(lines)

        if action == "read_text_file":
            header = [
                f"파일: {result.get('path', '')}",
                f"인코딩: {result.get('encoding', 'unknown')}",
                "",
            ]
            content = result.get("content", "")
            if result.get("truncated"):
                content += "\n\n... 파일이 커서 일부만 표시했습니다."
            return "\n".join(header) + content

        if action in {"git_status", "git_diff_stat", "git_diff_names", "git_diff"}:
            stdout = (result.get("stdout") or "").strip()
            stderr = (result.get("stderr") or "").strip()
            if stdout:
                return stdout
            if stderr:
                return stderr
            messages = {
                "git_status": "Git 변경 사항이 없습니다.",
                "git_diff_stat": "변경 통계가 없습니다.",
                "git_diff_names": "변경된 파일이 없습니다.",
                "git_diff": "표시할 코드 변경 내용이 없습니다.",
            }
            return messages[action]

        if action in {"python_version", "pip_version"}:
            return (result.get("stdout") or result.get("stderr") or "버전 정보를 찾지 못했습니다.").strip()

        return str(result)
