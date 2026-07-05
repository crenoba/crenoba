# providers/openrouter_provider.py

"""
CRENOBA OpenRouter Provider

v0.9.1 목표:
- Gemini 403 문제가 있을 때 OpenRouter를 대체 실제 AI Provider로 사용한다.
- OpenRouter의 OpenAI-compatible chat completions API를 호출한다.
- main.py / ai_client.py에서는 다른 Provider와 동일하게 generate(prompt)를 호출한다.
"""

import requests

from config import OPENROUTER_API_KEY, OPENROUTER_MODEL


class OpenRouterProvider:
    """
    OpenRouter 실제 API Provider.
    """

    def __init__(self):
        if not OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY is missing. "
                "Create a .env file and set OPENROUTER_API_KEY first."
            )

        self.model_name = OPENROUTER_MODEL or "openrouter/free"
        self.api_key = OPENROUTER_API_KEY
        self.endpoint = "https://openrouter.ai/api/v1/chat/completions"

    def generate(self, prompt: str) -> str:
        """
        OpenRouter API에 prompt를 보내고 text 응답을 반환한다.
        """
        if not prompt:
            return "입력 prompt가 비어 있습니다."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://127.0.0.1:8000",
            "X-Title": "CRENOBA Local Agent",
        }

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are CRENOBA, a Korean task, coding, study, "
                        "project, report, and Apollo assistant. "
                        "Answer in Korean unless the user asks otherwise."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        }

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=60,
            )

            if response.status_code != 200:
                return (
                    "# CRENOBA OpenRouter Provider Error\n\n"
                    "OpenRouter API 호출 중 오류가 발생했습니다.\n\n"
                    f"모델: {self.model_name}\n"
                    f"HTTP 상태 코드: {response.status_code}\n"
                    f"응답 내용: {response.text[:1000]}\n\n"
                    "확인할 것:\n"
                    "1. .env에 OPENROUTER_API_KEY가 들어갔는지 확인\n"
                    "2. OPENROUTER_MODEL 이름이 올바른지 확인\n"
                    "3. OpenRouter 무료 모델 사용 한도 또는 rate limit 확인\n"
                    "4. 인터넷 연결 상태 확인"
                )

            data = response.json()

            choices = data.get("choices", [])

            if not choices:
                return (
                    "# CRENOBA OpenRouter Provider Error\n\n"
                    "OpenRouter 응답에 choices가 없습니다.\n\n"
                    f"응답 내용: {data}"
                )

            message = choices[0].get("message", {})
            content = message.get("content", "")

            if content:
                return content

            return str(data)

        except Exception as e:
            return (
                "# CRENOBA OpenRouter Provider Error\n\n"
                "OpenRouter API 호출 중 예외가 발생했습니다.\n\n"
                f"모델: {self.model_name}\n"
                f"오류: {e}\n\n"
                "확인할 것:\n"
                "1. requests 패키지 설치 여부 확인\n"
                "2. .env의 OPENROUTER_API_KEY 확인\n"
                "3. 네트워크 연결 확인\n"
                "4. OPENROUTER_MODEL 값 확인"
            )

    def call(self, prompt: str) -> str:
        return self.generate(prompt)

    def run(self, prompt: str) -> str:
        return self.generate(prompt)


def generate_response(prompt: str) -> str:
    """
    함수형 호출도 지원하기 위한 진입점.
    """
    provider = OpenRouterProvider()
    return provider.generate(prompt)