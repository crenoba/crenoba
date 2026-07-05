def parse_command(message: str) -> dict:
    """
    사용자의 메시지에서 /crenoba 명령어와 내용을 분리한다.
    """

    message = message.strip()

    if not message.startswith("/crenoba"):
        return {
            "command": "chat",
            "content": message,
        }

    lines = message.splitlines()

    first_line = lines[0].strip()
    content = "\n".join(lines[1:]).strip()

    parts = first_line.split()

    if len(parts) < 2:
        return {
            "command": "unknown",
            "content": content,
        }

    command = parts[1].lower()

    return {
        "command": command,
        "content": content,
    }