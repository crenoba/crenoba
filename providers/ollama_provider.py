# providers/ollama_provider.py

"""
CRENOBA Ollama Provider

v0.9.2 목표:
- 외부 API 없이 데스크톱에서 로컬 LLM을 실행한다.
- Ollama local API를 통해 CRENOBA가 모델을 호출한다.
- main.py / ai_client.py에서는 다른 Provider와 동일하게 generate(prompt)를 호출한다.
"""

import requests

from config import OLLAMA_BASE_URL, OLLAMA_MODEL


class OllamaProvider:
    """
    Ollama 로컬 AI Provider.
    """

    def __init__(self):
        self.base_url = (OLLAMA_BASE_URL or "http://localhost:11434").rstrip("/")
        self.model_name = OLLAMA_MODEL or "qwen3-coder:30b"
        self.endpoint = f"{self.base_url}/api/chat"

    def generate(self, prompt: str) -> str:
        """
        Ollama 로컬 API에 prompt를 보내고 text 응답을 반환한다.
        """
        if not prompt:
            return "입력 prompt가 비어 있습니다."

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are CRENOBA, a Korean personal AI agent system. "
                        "You help with coding, project management, study plans, reports, "
                        "task planning, and Team Apollo engineering work. "
                        "Answer in Korean unless the user asks otherwise. "
                        "When code changes are needed, provide the full replacement code "
                        "for the relevant file whenever possible."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "stream": False,
        }

        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                timeout=300,
            )

            if response.status_code != 200:
                return (
                    "# CRENOBA Ollama Provider Error\n\n"
                    "Ollama 로컬 API 호출 중 오류가 발생했습니다.\n\n"
                    f"모델: {self.model_name}\n"
                    f"Base URL: {self.base_url}\n"
                    f"HTTP 상태 코드: {response.status_code}\n"
                    f"응답 내용: {response.text[:1000]}\n\n"
                    "확인할 것:\n"
                    "1. Ollama가 설치되어 실행 중인지 확인\n"
                    "2. PowerShell에서 `ollama list` 실행\n"
                    "3. `.env`의 OLLAMA_MODEL 이름이 실제 모델명과 같은지 확인\n"
                    "4. `ollama pull qwen3-coder:30b`가 완료됐는지 확인\n"
                    "5. http://localhost:11434/api/tags 접속 또는 Invoke-RestMethod로 확인"
                )

            data = response.json()

            message = data.get("message", {})
            content = message.get("content", "")

            if content:
                return content

            return str(data)

        except requests.exceptions.ConnectionError:
            return (
                "# CRENOBA Ollama Provider Error\n\n"
                "Ollama 서버에 연결할 수 없습니다.\n\n"
                f"Base URL: {self.base_url}\n"
                f"모델: {self.model_name}\n\n"
                "해결 방법:\n"
                "1. Ollama를 실행하세요.\n"
                "2. PowerShell에서 `ollama --version` 확인\n"
                "3. `Invoke-RestMethod http://localhost:11434/api/tags` 실행\n"
                "4. Ollama가 꺼져 있으면 시작 메뉴에서 Ollama를 실행하세요."
            )

        except requests.exceptions.Timeout:
            return (
                "# CRENOBA Ollama Provider Error\n\n"
                "Ollama 응답 시간이 너무 오래 걸려 timeout이 발생했습니다.\n\n"
                f"모델: {self.model_name}\n\n"
                "해결 방법:\n"
                "1. 더 작은 모델로 변경하세요. 예: qwen3:14b\n"
                "2. 처음 실행은 모델 로딩 때문에 오래 걸릴 수 있으니 다시 시도하세요.\n"
                "3. 작업 관리자를 열어 GPU/CPU/RAM 사용량을 확인하세요."
            )

        except Exception as e:
            return (
                "# CRENOBA Ollama Provider Error\n\n"
                "Ollama 로컬 API 호출 중 예외가 발생했습니다.\n\n"
                f"모델: {self.model_name}\n"
                f"Base URL: {self.base_url}\n"
                f"오류: {e}\n\n"
                "확인할 것:\n"
                "1. requests 패키지 설치 여부 확인\n"
                "2. OLLAMA_BASE_URL 값 확인\n"
                "3. OLLAMA_MODEL 값 확인\n"
                "4. Ollama 모델 다운로드 여부 확인"
            )

    def call(self, prompt: str) -> str:
        return self.generate(prompt)

    def run(self, prompt: str) -> str:
        return self.generate(prompt)


def generate_response(prompt: str) -> str:
    """
    함수형 호출도 지원하기 위한 진입점.
    """
    provider = OllamaProvider()
    return provider.generate(prompt)