from pathlib import Path

import pytest

from tools.test_tools import (
    CodeTestToolError,
    python_compile_all,
    python_compile_file,
)
from tools.tool_registry import TOOL_REGISTRY


def test_code_tools_are_registered() -> None:
    assert "python_compile_file" in TOOL_REGISTRY
    assert "python_compile_all" in TOOL_REGISTRY
    assert "run_pytest" in TOOL_REGISTRY


def test_python_compile_file_accepts_valid_python(tmp_path: Path) -> None:
    target = tmp_path / "valid_sample.py"
    target.write_text(
        "def add(a: int, b: int) -> int:\n"
        "    return a + b\n",
        encoding="utf-8",
    )

    result = python_compile_file(
        workspace_root=tmp_path,
        path="valid_sample.py",
    )

    assert result["success"] is True
    assert result["return_code"] == 0
    assert result["target"] == "valid_sample.py"


def test_python_compile_file_detects_syntax_error(tmp_path: Path) -> None:
    target = tmp_path / "invalid_sample.py"
    target.write_text(
        "def broken_function(\n"
        "    return True\n",
        encoding="utf-8",
    )

    result = python_compile_file(
        workspace_root=tmp_path,
        path="invalid_sample.py",
    )

    assert result["success"] is False
    assert result["return_code"] != 0
    assert "SyntaxError" in result["stderr"]


def test_python_compile_all_accepts_valid_directory(tmp_path: Path) -> None:
    package = tmp_path / "sample_package"
    package.mkdir()

    target = package / "module.py"
    target.write_text(
        "VALUE = 10\n",
        encoding="utf-8",
    )

    result = python_compile_all(
        workspace_root=tmp_path,
        path="sample_package",
    )

    assert result["success"] is True
    assert result["return_code"] == 0
    assert result["target"] == "sample_package"


def test_python_compile_file_blocks_outside_workspace(tmp_path: Path) -> None:
    outside_file = Path(__file__).resolve()

    with pytest.raises(CodeTestToolError):
        python_compile_file(
            workspace_root=tmp_path,
            path=str(outside_file),
        )