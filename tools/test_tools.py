from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.file_tools import resolve_workspace_path
from tools.shell_tools import run_command


# 이 파일은 CRENOBA 실행 도구이며 pytest 테스트 파일이 아닙니다.
__test__ = False


class CodeTestToolError(RuntimeError):
    pass


def _resolve_from_cwd(
    workspace_root: Path,
    cwd: str,
    target: str,
) -> Path:
    root = workspace_root.resolve()
    working_directory = resolve_workspace_path(root, cwd)

    candidate = Path(target).expanduser()
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (working_directory / candidate).resolve()

    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise CodeTestToolError(
            "프로젝트 작업 폴더 밖의 경로에는 접근할 수 없습니다."
        ) from exc

    return resolved


def _display_path(workspace_root: Path, path: Path) -> str:
    try:
        return path.relative_to(workspace_root.resolve()).as_posix()
    except ValueError:
        return str(path)


def python_compile_file(
    workspace_root: Path,
    path: str,
    cwd: str = ".",
    timeout_sec: int = 20,
) -> dict[str, Any]:
    """하나의 Python 파일을 py_compile로 검사합니다."""

    target = _resolve_from_cwd(workspace_root, cwd, path)

    if not target.exists():
        raise CodeTestToolError(f"검사할 파일을 찾을 수 없습니다: {path}")

    if not target.is_file():
        raise CodeTestToolError(f"파일 경로가 아닙니다: {path}")

    if target.suffix.lower() != ".py":
        raise CodeTestToolError("Python 문법 검사는 .py 파일만 지원합니다.")

    result = run_command(
        workspace_root=workspace_root,
        command=["python", "-m", "py_compile", str(target)],
        cwd=cwd,
        timeout_sec=timeout_sec,
    )

    return {
        **result,
        "check_type": "python_compile_file",
        "target": _display_path(workspace_root, target),
    }


def python_compile_all(
    workspace_root: Path,
    path: str = ".",
    cwd: str = ".",
    timeout_sec: int = 60,
) -> dict[str, Any]:
    """지정 폴더 아래의 Python 파일을 compileall로 검사합니다."""

    target = _resolve_from_cwd(workspace_root, cwd, path)

    if not target.exists():
        raise CodeTestToolError(f"검사할 경로를 찾을 수 없습니다: {path}")

    if not target.is_dir():
        raise CodeTestToolError(f"폴더 경로가 아닙니다: {path}")

    result = run_command(
        workspace_root=workspace_root,
        command=["python", "-m", "compileall", "-q", str(target)],
        cwd=cwd,
        timeout_sec=timeout_sec,
    )

    return {
        **result,
        "check_type": "python_compile_all",
        "target": _display_path(workspace_root, target),
    }


def run_pytest(
    workspace_root: Path,
    cwd: str = ".",
    path: str | None = None,
    timeout_sec: int = 60,
) -> dict[str, Any]:
    """임의 옵션 없이 안전하게 pytest를 실행합니다."""

    command = ["python", "-m", "pytest", "-q"]
    display_target = "."

    if path:
        target = _resolve_from_cwd(workspace_root, cwd, path)

        if not target.exists():
            raise CodeTestToolError(f"테스트 대상을 찾을 수 없습니다: {path}")

        command.append(str(target))
        display_target = _display_path(workspace_root, target)

    result = run_command(
        workspace_root=workspace_root,
        command=command,
        cwd=cwd,
        timeout_sec=timeout_sec,
    )

    return {
        **result,
        "check_type": "pytest",
        "target": display_target,
    }