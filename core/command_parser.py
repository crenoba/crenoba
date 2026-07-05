# core/command_parser.py

"""
CRENOBA Command Parser

역할:
- 사용자가 입력한 /crenoba 명령어를 분석한다.
- main.py에서 사용할 mode 값을 안정적으로 반환한다.

v0.7.3 수정:
- 여러 줄 입력에서도 첫 줄의 명령어를 정확히 감지한다.
- /crenoba task 입력이 반드시 mode="task"로 반환되도록 한다.
"""


VALID_CREN0BA_MODES = {
    "task",
    "study",
    "code",
    "report",
    "project",
    "apollo",
    "relay",
}


def _get_first_line(text: str) -> str:
    if not text:
        return ""

    return text.strip().splitlines()[0].strip()


def _clean_prompt(text: str, mode: str) -> str:
    """
    입력에서 첫 줄 명령어만 제거하고 실제 내용만 남긴다.
    """
    if not text:
        return ""

    lines = text.strip().splitlines()

    if not lines:
        return ""

    first_line = lines[0].strip().lower()

    command = f"/crenoba {mode}"

    if first_line.startswith(command):
        return "\n".join(lines[1:]).strip()

    return text.strip()


def parse_command(text: str) -> dict:
    """
    사용자 입력을 분석해서 command/mode/agent 정보를 반환한다.

    반환 예:
    {
        "command": "/crenoba task",
        "mode": "task",
        "agent": "task",
        "raw": "...",
        "cleaned": "..."
    }
    """
    raw_text = text or ""
    first_line = _get_first_line(raw_text)
    lowered = first_line.lower()

    if lowered.startswith("/crenoba"):
        parts = lowered.split()

        if len(parts) >= 2:
            mode = parts[1].strip()

            if mode in VALID_CREN0BA_MODES:
                return {
                    "command": f"/crenoba {mode}",
                    "mode": mode,
                    "agent": mode,
                    "raw": raw_text,
                    "cleaned": _clean_prompt(raw_text, mode),
                }

        return {
            "command": "/crenoba",
            "mode": "general",
            "agent": "general",
            "raw": raw_text,
            "cleaned": raw_text.strip(),
        }

    if lowered.startswith("/gpt"):
        return {
            "command": "/gpt",
            "mode": "gpt",
            "agent": "gpt",
            "raw": raw_text,
            "cleaned": raw_text.strip(),
        }

    return {
        "command": "plain",
        "mode": "general",
        "agent": "general",
        "raw": raw_text,
        "cleaned": raw_text.strip(),
    }