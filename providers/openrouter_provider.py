import os
import requests


class OpenRouterProvider:
    """
    CRENOBA OpenRouter Provider
    """

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.default_model = os.getenv("OPENROUTER_MODEL", "openrouter/free")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def generate(
        self,
        prompt: str,
        model_override: str | None = None,
        agent: str = "general",
        mode: str = "general",
    ) -> str:
        if not self.api_key:
            return (
                "[CRENOBA OpenRouter Error]\n"
                "OPENROUTER_API_KEY가 .env에 설정되어 있지 않습니다."
            )

        model = model_override or self.default_model

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "CRENOBA",
        }

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": self._build_system_prompt(agent, mode),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.2,
            "max_tokens": 800,
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=120,
            )

            if response.status_code != 200:
                return (
                    "[CRENOBA OpenRouter Error]\n"
                    f"Status Code: {response.status_code}\n"
                    f"Response: {response.text}"
                )

            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

        except requests.exceptions.Timeout:
            return (
                "[CRENOBA OpenRouter Timeout]\n"
                "OpenRouter 응답 시간이 너무 오래 걸렸습니다."
            )

        except Exception as e:
            return f"[CRENOBA OpenRouter Unknown Error]\n{str(e)}"

    def _build_system_prompt(self, agent: str, mode: str) -> str:
        return f"""
너는 CRENOBA의 {agent} Agent다.
항상 한국어로 답한다.
사용자의 요청을 실무적으로 처리한다.
코드 수정이 필요하면 관련 파일 전체 코드를 제공한다.
현재 mode는 {mode}다.
""".strip()

    def call(self, prompt: str) -> str:
        return self.generate(prompt)

    def run(self, prompt: str) -> str:
        return self.generate(prompt)


def generate_response(prompt: str) -> str:
    return OpenRouterProvider().generate(prompt)