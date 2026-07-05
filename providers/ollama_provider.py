# providers/ollama_provider.py

"""
CRENOBA Ollama Provider

v0.9.3 목표:
- 외부 API 없이 데스크톱에서 로컬 LLM을 실행한다.
- Ollama local API를 통해 CRENOBA가 모델을 호출한다.
- 로컬 모델이 너무 길게 답하지 않도록 출력 길이를 제한한다.
- keep_alive로 모델을 일정 시간 메모리에 유지해 반복 호출 속도를 개선한다.
"""

import requests

from config import OLLAMA_BASE_URL, OLLAMA_MODEL


class OllamaProvider:
    """
    Ollama 로컬 AI Provider.
    """

    def __init__(self):
        self.base_url = (OLLAMA_BASE_URL or "http://localhost:11434").rstrip("/")
        self.model_name = OLLAMA_MODEL or "qwen2.5-coder:7b-instruct"
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
                        "너는 CRENOBA 로컬 AI Agent다. "
                        "사용자의 업무, 코딩, 공부, 프로젝트 관리를 돕는다. "
                        "항상 한국어로 답한다. "
                        "사용자가 짧게 답하라고 하면 반드시 1~3문장만 답한다. "
                        "사용자의 문장을 확대해석하지 말고, 요청한 내용에만 답한다. "
                        "코드 수정이 필요하면 가능한 한 관련 파일 전체 코드를 제공한다."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "stream": False,
            "keep_alive": "30m",
            "options": {
                "temperature": 0.2,
                "num_predict": 300,
                "num_ctx": 4096,
            },
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
                    "2. PowerShell에서 `Invoke-RestMethod http://localhost:11434/api/tags` 실행\n"
                    "3. `.env`의 OLLAMA_MODEL 이름이 실제 모델명과 같은지 확인\n"
                    "4. 모델 다운로드가 완료됐는지 확인"
                )

            data = response.json()

            message = data.get("message", {})
            content = message.get("content", "")

            if content:
                return content.strip()

            return str(data)

        except requests.exceptions.ConnectionError:
            return (
                "# CRENOBA Ollama Provider Error\n\n"
                "Ollama 서버에 연결할 수 없습니다.\n\n"
                f"Base URL: {self.base_url}\n"
                f"모델: {self.model_name}\n\n"
                "해결 방법:\n"
                "1. Ollama를 실행하세요.\n"
                "2. `Invoke-RestMethod http://localhost:11434/api/tags` 실행\n"
                "3. Ollama가 꺼져 있으면 시작 메뉴에서 Ollama를 실행하세요."
            )

        except requests.exceptions.Timeout:
            return (
                "# CRENOBA Ollama Provider Error\n\n"
                "Ollama 응답 시간이 너무 오래 걸려 timeout이 발생했습니다.\n\n"
                f"모델: {self.model_name}\n\n"
                "해결 방법:\n"
                "1. 더 작은 모델로 변경하세요. 예: qwen2.5-coder:7b-instruct 또는 gemma3:4b\n"
                "2. 처음 실행은 모델 로딩 때문에 오래 걸릴 수 있으니 다시 시도하세요.\n"
                "3. 작업 관리자에서 GPU/CPU/RAM 사용량을 확인하세요."
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