from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from tools.file_tools import resolve_workspace_path
from tools.shell_tools import run_command


SENSITIVE_GIT_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "secrets.json",
}


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
        _validate_git_paths(workspace_root, cwd, [path])
        command.append(path)
    return run_command(workspace_root, command, cwd=cwd)


def preview_git_add(
    workspace_root: Path,
    cwd: str = ".",
    paths: list[str] | None = None,
) -> dict[str, Any]:
    selected_paths = paths or ["."]
    _validate_git_paths(workspace_root, cwd, selected_paths)

    status = _require_success(
        _git_status_for_approval(workspace_root, cwd),
        "Git 상태를 확인하지 못했습니다.",
    )
    status_text = status.get("stdout", "")
    if not status_text.strip():
        raise RuntimeError("스테이징할 변경 파일이 없습니다.")

    sensitive = _find_sensitive_status_paths(status_text)

    return {
        "cwd": cwd,
        "paths": selected_paths,
        "operation": "git add",
        "status_before": status_text,
        "status_sha256": _sha256(status_text),
        "automatic_exclusions": [".crenoba/**", "data/action_logs.jsonl", ".env*"],
        "sensitive_excluded": sensitive,
    }


def git_add(
    workspace_root: Path,
    cwd: str = ".",
    paths: list[str] | None = None,
    expected_status_sha256: str | None = None,
) -> dict[str, Any]:
    selected_paths = paths or ["."]
    _validate_git_paths(workspace_root, cwd, selected_paths)

    current = _require_success(
        _git_status_for_approval(workspace_root, cwd),
        "Git 상태를 확인하지 못했습니다.",
    )
    current_text = current.get("stdout", "")
    if _sha256(current_text) != expected_status_sha256:
        raise RuntimeError(
            "승인 미리보기 이후 Git 변경 상태가 달라졌습니다. 다시 요청해주세요."
        )

    if selected_paths == ["."]:
        command = [
            "git",
            "add",
            "--all",
            "--",
            ".",
            ":(exclude).crenoba/**",
            ":(exclude)data/action_logs.jsonl",
            ":(exclude).env*",
        ]
    else:
        command = ["git", "add", "--", *selected_paths]

    execution = _require_success(
        run_command(workspace_root, command, cwd=cwd),
        "git add 실행에 실패했습니다.",
    )
    status_after = _require_success(
        run_command(workspace_root, ["git", "status", "--short"], cwd=cwd),
        "스테이징 후 상태를 확인하지 못했습니다.",
    )
    return {
        **execution,
        "paths": selected_paths,
        "status_after": status_after.get("stdout", ""),
    }


def preview_git_commit(
    workspace_root: Path,
    cwd: str = ".",
    message: str = "",
) -> dict[str, Any]:
    clean_message = _validate_commit_message(message)
    staged_names = _require_success(
        run_command(workspace_root, ["git", "diff", "--cached", "--name-status"], cwd=cwd),
        "스테이징된 파일을 확인하지 못했습니다.",
    )
    staged_text = staged_names.get("stdout", "")
    if not staged_text.strip():
        raise RuntimeError("커밋할 스테이징 파일이 없습니다. 먼저 git add 작업을 실행해주세요.")

    sensitive = _find_sensitive_status_paths(staged_text)
    if sensitive:
        raise RuntimeError(
            "민감할 수 있는 파일이 스테이징되어 있어 커밋을 중단했습니다: "
            + ", ".join(sensitive)
        )

    staged_stat = _require_success(
        run_command(workspace_root, ["git", "diff", "--cached", "--stat"], cwd=cwd),
        "스테이징 변경 통계를 확인하지 못했습니다.",
    )
    staged_binary = _require_success(
        run_command(workspace_root, ["git", "diff", "--cached", "--binary"], cwd=cwd),
        "스테이징 변경 해시를 계산하지 못했습니다.",
    )
    return {
        "cwd": cwd,
        "operation": "git commit",
        "message": clean_message,
        "staged_files": staged_text,
        "staged_stat": staged_stat.get("stdout", ""),
        "staged_sha256": _sha256(staged_binary.get("stdout", "")),
    }


def git_commit(
    workspace_root: Path,
    cwd: str = ".",
    message: str = "",
    expected_staged_sha256: str | None = None,
) -> dict[str, Any]:
    clean_message = _validate_commit_message(message)
    staged_binary = _require_success(
        run_command(workspace_root, ["git", "diff", "--cached", "--binary"], cwd=cwd),
        "스테이징 변경 상태를 확인하지 못했습니다.",
    )
    current_hash = _sha256(staged_binary.get("stdout", ""))
    if current_hash != expected_staged_sha256:
        raise RuntimeError(
            "승인 미리보기 이후 스테이징 내용이 달라졌습니다. 다시 요청해주세요."
        )

    execution = _require_success(
        run_command(workspace_root, ["git", "commit", "-m", clean_message], cwd=cwd, timeout_sec=60),
        "git commit 실행에 실패했습니다.",
    )
    latest = _require_success(
        run_command(workspace_root, ["git", "log", "-1", "--oneline"], cwd=cwd),
        "생성된 커밋을 확인하지 못했습니다.",
    )
    return {
        **execution,
        "message": clean_message,
        "latest_commit": latest.get("stdout", ""),
    }


def _git_status_for_approval(workspace_root: Path, cwd: str) -> dict[str, Any]:
    return run_command(
        workspace_root,
        [
            "git",
            "status",
            "--short",
            "--",
            ".",
            ":(exclude).crenoba/**",
            ":(exclude)data/action_logs.jsonl",
        ],
        cwd=cwd,
    )


def _validate_git_paths(workspace_root: Path, cwd: str, paths: list[str]) -> None:
    working_directory = resolve_workspace_path(workspace_root, cwd)
    if not working_directory.is_dir():
        raise RuntimeError(f"Git 실행 폴더가 아닙니다: {cwd}")

    for path in paths:
        if not isinstance(path, str) or not path.strip():
            raise RuntimeError("Git 경로가 올바르지 않습니다.")
        cleaned = path.strip()
        if cleaned.startswith("-"):
            raise RuntimeError("옵션처럼 해석될 수 있는 Git 경로는 사용할 수 없습니다.")
        candidate = (working_directory / cleaned).resolve()
        try:
            candidate.relative_to(workspace_root.resolve())
        except ValueError as exc:
            raise RuntimeError("작업 폴더 밖의 파일은 Git 작업 대상으로 지정할 수 없습니다.") from exc
        if Path(cleaned).name.lower() in SENSITIVE_GIT_NAMES:
            raise RuntimeError("환경 변수·자격 증명 파일은 Git 작업 대상으로 지정할 수 없습니다.")


def _validate_commit_message(message: str) -> str:
    clean = (message or "").strip()
    if not clean:
        raise RuntimeError("커밋 메시지를 입력해주세요.")
    if "\n" in clean or "\r" in clean:
        raise RuntimeError("현재 버전에서는 한 줄 커밋 메시지만 사용할 수 있습니다.")
    if len(clean) > 120:
        raise RuntimeError("커밋 메시지는 120자 이하로 입력해주세요.")
    return clean


def _find_sensitive_status_paths(status_text: str) -> list[str]:
    found: list[str] = []
    for line in status_text.splitlines():
        path_text = line[3:].strip() if len(line) >= 4 else line.strip()
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1]
        name = Path(path_text).name.lower()
        if name in SENSITIVE_GIT_NAMES or name.startswith(".env"):
            found.append(path_text)
    return found


def _require_success(result: dict[str, Any], fallback_message: str) -> dict[str, Any]:
    if not result.get("success", False):
        detail = result.get("stderr") or result.get("stdout") or fallback_message
        raise RuntimeError(str(detail))
    return result


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
