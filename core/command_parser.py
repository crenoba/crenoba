# =========================
# CRENOBA COMMAND PARSER
# v0.9.6
# =========================

SUPPORTED_AGENTS = {
    "task",
    "study",
    "code",
    "report",
    "project",
    "apollo",
    "relay",
    "general",
}


def parse_command(prompt: str) -> dict:
    """
    사용자 입력에서 CRENOBA 명령어를 분석한다.

    예:
    /crenoba code
    파이썬 에러 고쳐줘

    결과:
    {
        "command": "/crenoba code",
        "mode": "code",
        "agent": "code",
        "content": "파이썬 에러 고쳐줘"
    }
    """

    if not prompt:
        return _default_result("")

    raw_text = prompt.strip()
    lines = raw_text.splitlines()

    first_line = lines[0].strip()
    rest_lines = lines[1:]

    tokens = first_line.split()

    if not tokens:
        return _default_result(raw_text)

    first_token = tokens[0].lower()

    # =========================
    # /crenoba <agent>
    # =========================

    if first_token == "/crenoba":
        if len(tokens) >= 2:
            candidate_agent = tokens[1].lower()

            if candidate_agent in SUPPORTED_AGENTS:
                inline_content = " ".join(tokens[2:]).strip()
                rest_content = "\n".join(rest_lines).strip()
                content = _join_content(inline_content, rest_content)

                return {
                    "command": f"/crenoba {candidate_agent}",
                    "mode": candidate_agent,
                    "agent": candidate_agent,
                    "content": content,
                }

        return {
            "command": "/crenoba",
            "mode": "general",
            "agent": "general",
            "content": "\n".join(rest_lines).strip(),
        }

    # =========================
    # Short commands: /code, /task ...
    # =========================

    if first_token.startswith("/"):
        candidate_agent = first_token.replace("/", "").strip().lower()

        if candidate_agent in SUPPORTED_AGENTS:
            inline_content = " ".join(tokens[1:]).strip()
            rest_content = "\n".join(rest_lines).strip()
            content = _join_content(inline_content, rest_content)

            return {
                "command": first_token,
                "mode": candidate_agent,
                "agent": candidate_agent,
                "content": content,
            }

    # =========================
    # GPT workflow commands
    # =========================

    if first_token == "/gpt":
        if len(tokens) >= 2:
            gpt_command = tokens[1].lower()

            if gpt_command == "relay":
                return {
                    "command": "/gpt relay",
                    "mode": "relay",
                    "agent": "relay",
                    "content": raw_text,
                }

            if gpt_command == "finish":
                return {
                    "command": "/gpt finish",
                    "mode": "project",
                    "agent": "project",
                    "content": raw_text,
                }

            if gpt_command == "restore":
                return {
                    "command": "/gpt restore",
                    "mode": "relay",
                    "agent": "relay",
                    "content": raw_text,
                }

    return _default_result(raw_text)


def _default_result(content: str) -> dict:
    return {
        "command": None,
        "mode": "general",
        "agent": "general",
        "content": content,
    }


def _join_content(inline_content: str, rest_content: str) -> str:
    if inline_content and rest_content:
        return f"{inline_content}\n{rest_content}"

    if inline_content:
        return inline_content

    if rest_content:
        return rest_content

    return ""