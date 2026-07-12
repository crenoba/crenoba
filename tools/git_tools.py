from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.shell_tools import run_command


def git_status(workspace_root: Path, cwd: str = ".") -> dict[str, Any]:
    return run_command(
        workspace_root,
        ["git", "status", "--short", "--branch"],
        cwd=cwd,
    )


def git_diff_stat(workspace_root: Path, cwd: str = ".") -> dict[str, Any]:
    return run_command(
        workspace_root,
        ["git", "diff", "--stat"],
        cwd=cwd,
    )


def git_diff_names(workspace_root: Path, cwd: str = ".") -> dict[str, Any]:
    return run_command(
        workspace_root,
        ["git", "diff", "--name-status"],
        cwd=cwd,
    )


def git_diff(
    workspace_root: Path,
    cwd: str = ".",
    path: str | None = None,
) -> dict[str, Any]:
    command = ["git", "diff", "--"]
    if path:
        command.append(path)
    return run_command(workspace_root, command, cwd=cwd)
