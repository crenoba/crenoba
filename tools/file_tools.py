from __future__ import annotations

from pathlib import Path
from typing import Any


DEFAULT_MAX_FILE_BYTES = 200_000
DEFAULT_MAX_RESULTS = 200


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

    ignored_parts = {".git", ".venv", "__pycache__", "node_modules"}
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

    try:
        content = raw.decode("utf-8")
        encoding = "utf-8"
    except UnicodeDecodeError:
        try:
            content = raw.decode("cp949")
            encoding = "cp949"
        except UnicodeDecodeError as exc:
            raise FileToolError(
                "현재 버전에서는 텍스트 파일만 읽을 수 있습니다."
            ) from exc

    return {
        "path": target.relative_to(workspace_root.resolve()).as_posix(),
        "encoding": encoding,
        "content": content,
        "size_bytes": target.stat().st_size,
        "truncated": truncated,
    }
