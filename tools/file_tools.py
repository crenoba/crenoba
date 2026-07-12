from __future__ import annotations

import difflib
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


DEFAULT_MAX_FILE_BYTES = 200_000
DEFAULT_MAX_RESULTS = 200
WRITABLE_TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".html",
    ".css",
    ".json",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".log",
    ".csv",
    ".xml",
}
SENSITIVE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "secrets.json",
}


class WorkspaceViolationError(ValueError):
    pass


class FileToolError(RuntimeError):
    pass


def resolve_workspace_path(workspace_root: Path, requested_path: str | None = None) -> Path:
    root = workspace_root.resolve()
    candidate = root if not requested_path else (root / requested_path).resolve()

    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise WorkspaceViolationError(
            "작업 폴더 밖의 경로에는 접근할 수 없습니다."
        ) from exc

    return candidate


def list_files(
    workspace_root: Path,
    path: str = ".",
    recursive: bool = True,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> dict[str, Any]:
    target = resolve_workspace_path(workspace_root, path)
    if not target.exists():
        raise FileToolError(f"경로를 찾을 수 없습니다: {path}")
    if not target.is_dir():
        raise FileToolError(f"폴더가 아닙니다: {path}")

    max_results = max(1, min(max_results, 1000))
    iterator = target.rglob("*") if recursive else target.iterdir()

    ignored_parts = {".git", ".venv", "__pycache__", "node_modules", ".crenoba"}
    items: list[dict[str, Any]] = []
    truncated = False

    for item in iterator:
        relative = item.relative_to(workspace_root.resolve())
        if any(part in ignored_parts for part in relative.parts):
            continue

        items.append(
            {
                "path": relative.as_posix(),
                "type": "directory" if item.is_dir() else "file",
                "size_bytes": item.stat().st_size if item.is_file() else None,
            }
        )

        if len(items) >= max_results:
            truncated = True
            break

    items.sort(key=lambda entry: (entry["type"] != "directory", entry["path"].lower()))
    return {
        "workspace": str(workspace_root.resolve()),
        "requested_path": path,
        "items": items,
        "count": len(items),
        "truncated": truncated,
    }


def read_text_file(
    workspace_root: Path,
    path: str,
    max_bytes: int = DEFAULT_MAX_FILE_BYTES,
) -> dict[str, Any]:
    target = resolve_workspace_path(workspace_root, path)
    if not target.exists():
        raise FileToolError(f"파일을 찾을 수 없습니다: {path}")
    if not target.is_file():
        raise FileToolError(f"파일이 아닙니다: {path}")

    max_bytes = max(1, min(max_bytes, 1_000_000))
    raw = target.read_bytes()
    truncated = len(raw) > max_bytes
    raw = raw[:max_bytes]
    content, encoding = _decode_text(raw)

    return {
        "path": target.relative_to(workspace_root.resolve()).as_posix(),
        "encoding": encoding,
        "content": content,
        "size_bytes": target.stat().st_size,
        "truncated": truncated,
    }


def preview_write_text_file(
    workspace_root: Path,
    path: str,
    content: str,
) -> dict[str, Any]:
    target = _validate_writable_target(workspace_root, path, content)
    existed = target.exists()
    old_content = ""
    encoding = "utf-8"

    if existed:
        if not target.is_file():
            raise FileToolError(f"파일이 아닙니다: {path}")
        raw = target.read_bytes()
        if len(raw) > DEFAULT_MAX_FILE_BYTES:
            raise FileToolError("현재 버전에서는 200KB 이하의 텍스트 파일만 수정할 수 있습니다.")
        old_content, encoding = _decode_text(raw)

    before_sha256 = _sha256_text(old_content) if existed else None
    after_sha256 = _sha256_text(content)
    diff_lines = difflib.unified_diff(
        old_content.splitlines(keepends=True),
        content.splitlines(keepends=True),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        lineterm="",
    )
    diff = "\n".join(diff_lines)
    if len(diff) > 30_000:
        diff = diff[:30_000] + "\n... 미리보기가 길어 일부만 표시했습니다."

    return {
        "path": target.relative_to(workspace_root.resolve()).as_posix(),
        "operation": "replace" if existed else "create",
        "existed": existed,
        "encoding": encoding,
        "before_sha256": before_sha256,
        "after_sha256": after_sha256,
        "before_bytes": len(old_content.encode("utf-8")),
        "after_bytes": len(content.encode("utf-8")),
        "diff": diff or "변경 내용이 없습니다.",
    }


def write_text_file(
    workspace_root: Path,
    path: str,
    content: str,
    expected_before_sha256: str | None = None,
) -> dict[str, Any]:
    target = _validate_writable_target(workspace_root, path, content)
    existed = target.exists()
    old_content = ""

    if existed:
        if not target.is_file():
            raise FileToolError(f"파일이 아닙니다: {path}")
        raw = target.read_bytes()
        old_content, _ = _decode_text(raw)
        current_hash = _sha256_text(old_content)
        if current_hash != expected_before_sha256:
            raise FileToolError(
                "미리보기 이후 파일 내용이 변경되었습니다. 안전을 위해 실행을 중단했습니다. 다시 요청해주세요."
            )
    elif expected_before_sha256 is not None:
        raise FileToolError(
            "미리보기 이후 파일 상태가 변경되었습니다. 안전을 위해 실행을 중단했습니다."
        )

    backup_path: str | None = None
    if existed:
        backup_path = _create_backup(workspace_root, target, old_content)

    target.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        dir=target.parent,
        delete=False,
        prefix=f".{target.name}.",
        suffix=".crenoba.tmp",
    ) as temp_file:
        temp_file.write(content)
        temp_path = Path(temp_file.name)

    try:
        os.replace(temp_path, target)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)

    return {
        "path": target.relative_to(workspace_root.resolve()).as_posix(),
        "operation": "replaced" if existed else "created",
        "size_bytes": target.stat().st_size,
        "sha256": _sha256_text(content),
        "backup_path": backup_path,
    }


def _validate_writable_target(workspace_root: Path, path: str, content: str) -> Path:
    if not isinstance(content, str):
        raise FileToolError("파일 내용은 문자열이어야 합니다.")
    encoded = content.encode("utf-8")
    if len(encoded) > DEFAULT_MAX_FILE_BYTES:
        raise FileToolError("현재 버전에서는 200KB 이하의 텍스트만 저장할 수 있습니다.")

    target = resolve_workspace_path(workspace_root, path)
    if target.name.lower() in SENSITIVE_NAMES:
        raise FileToolError("환경 변수·자격 증명 파일은 Computer Agent가 수정할 수 없습니다.")
    if target.suffix.lower() not in WRITABLE_TEXT_EXTENSIONS:
        raise FileToolError(
            "현재 버전에서는 안전 목록에 포함된 텍스트 파일 확장자만 수정할 수 있습니다."
        )
    if ".git" in target.relative_to(workspace_root.resolve()).parts:
        raise FileToolError(".git 내부 파일은 수정할 수 없습니다.")
    return target


def _decode_text(raw: bytes) -> tuple[str, str]:
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        try:
            return raw.decode("cp949"), "cp949"
        except UnicodeDecodeError as exc:
            raise FileToolError("현재 버전에서는 텍스트 파일만 처리할 수 있습니다.") from exc


def _sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _create_backup(workspace_root: Path, target: Path, old_content: str) -> str:
    relative = target.relative_to(workspace_root.resolve())
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = workspace_root.resolve() / ".crenoba" / "backups" / timestamp
    backup_target = backup_root / relative
    backup_target.parent.mkdir(parents=True, exist_ok=True)
    backup_target.write_text(old_content, encoding="utf-8", newline="")
    return backup_target.relative_to(workspace_root.resolve()).as_posix()
