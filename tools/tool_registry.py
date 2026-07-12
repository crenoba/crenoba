from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from tools.file_tools import list_files, read_text_file, write_text_file
from tools.git_tools import (
    git_add,
    git_commit,
    git_diff,
    git_diff_names,
    git_diff_stat,
    git_status,
)
from tools.shell_tools import pip_version, python_version


ToolFunction = Callable[..., dict[str, Any]]


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    function: ToolFunction


TOOL_REGISTRY: dict[str, ToolDefinition] = {
    "list_files": ToolDefinition(
        name="list_files",
        description="작업 폴더 안의 파일과 폴더 목록을 조회합니다.",
        function=list_files,
    ),
    "read_text_file": ToolDefinition(
        name="read_text_file",
        description="작업 폴더 안의 텍스트 파일을 읽습니다.",
        function=read_text_file,
    ),
    "write_text_file": ToolDefinition(
        name="write_text_file",
        description="승인 후 작업 폴더 안의 텍스트 파일을 생성하거나 전체 교체합니다.",
        function=write_text_file,
    ),
    "git_status": ToolDefinition(
        name="git_status",
        description="현재 Git 브랜치와 변경 파일을 조회합니다.",
        function=git_status,
    ),
    "git_diff_stat": ToolDefinition(
        name="git_diff_stat",
        description="Git 변경 사항의 통계를 조회합니다.",
        function=git_diff_stat,
    ),
    "git_diff_names": ToolDefinition(
        name="git_diff_names",
        description="Git에서 변경된 파일 이름과 상태를 조회합니다.",
        function=git_diff_names,
    ),
    "git_diff": ToolDefinition(
        name="git_diff",
        description="Git 변경 내용을 텍스트 diff로 조회합니다.",
        function=git_diff,
    ),
    "git_add": ToolDefinition(
        name="git_add",
        description="승인 후 지정한 변경 파일을 Git staging area에 추가합니다.",
        function=git_add,
    ),
    "git_commit": ToolDefinition(
        name="git_commit",
        description="승인 후 현재 staging area의 변경 사항을 커밋합니다.",
        function=git_commit,
    ),
    "python_version": ToolDefinition(
        name="python_version",
        description="현재 Python 버전을 조회합니다.",
        function=python_version,
    ),
    "pip_version": ToolDefinition(
        name="pip_version",
        description="현재 pip 버전을 조회합니다.",
        function=pip_version,
    ),
}


def list_registered_tools() -> list[dict[str, str]]:
    return [
        {"name": definition.name, "description": definition.description}
        for definition in TOOL_REGISTRY.values()
    ]


def execute_registered_tool(
    tool_name: str,
    workspace_root: Path,
    arguments: dict[str, Any] | None = None,
) -> dict[str, Any]:
    definition = TOOL_REGISTRY.get(tool_name)
    if definition is None:
        raise KeyError(f"등록되지 않은 도구입니다: {tool_name}")

    safe_arguments = dict(arguments or {})
    return definition.function(workspace_root=workspace_root, **safe_arguments)
