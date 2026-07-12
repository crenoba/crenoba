from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from tools.file_tools import resolve_workspace_path


class ShellToolError(RuntimeError):
    pass


def run_command(
    workspace_root: Path,
    command: list[str],
    cwd: str = ".",
    timeout_sec: int = 20,
) -> dict[str, Any]:
    """Run a pre-constructed command without invoking a shell."""

    if not command or any(not isinstance(part, str) or not part for part in command):
        raise ShellToolError("실행 명령 형식이 올바르지 않습니다.")

    working_directory = resolve_workspace_path(workspace_root, cwd)
    if not working_directory.is_dir():
        raise ShellToolError(f"실행 폴더가 아닙니다: {cwd}")

    timeout_sec = max(1, min(timeout_sec, 60))

    try:
        completed = subprocess.run(
            command,
            cwd=working_directory,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
            shell=False,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ShellToolError(f"프로그램을 찾을 수 없습니다: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ShellToolError(f"명령 실행 시간이 {timeout_sec}초를 초과했습니다.") from exc
    except OSError as exc:
        raise ShellToolError(f"명령 실행에 실패했습니다: {exc}") from exc

    return {
        "command": command,
        "cwd": str(working_directory),
        "return_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "success": completed.returncode == 0,
    }


def python_version(workspace_root: Path) -> dict[str, Any]:
    return run_command(workspace_root, ["python", "--version"])


def pip_version(workspace_root: Path) -> dict[str, Any]:
    return run_command(workspace_root, ["python", "-m", "pip", "--version"])
