# providers/gemini_provider.py

"""
CRENOBA Gemini Provider

v0.9 목표:
- Google GenAI SDK를 사용해 실제 Gemini API를 호출한다.
- main.py / ai_client.py에서는 MockProvider와 같은 방식으로 generate(prompt)를 호출한다.
- API Key가 없거나 호출 실패 시 이해하기 쉬운 에러 메시지를 반환한다.
"""

from google import genai

from config import GEMINI_API_KEY, GEMINI_MODEL


class GeminiProvider:
    """
    Gemini 실제 API Provider.
    """

    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is missing. "
                "Create a .env file and set GEMINI_API_KEY first."
            )

        self.model_name = GEMINI_MODEL or "gemini-2.5-flash-lite"
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def generate(self, prompt: str) -> str:
        """
        Gemini API에 prompt를 보내고 text 응답을 반환한다.
        """
        if not prompt:
            return "입력 prompt가 비어 있습니다."

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )

            if hasattr(response, "text") and response.text:
                return response.text

            return str(response)

        except Exception as e:
            return (
                "# CRENOBA Gemini Provider Error\n\n"
                "Gemini API 호출 중 오류가 발생했습니다.\n\n"
                f"모델: {self.model_name}\n"
                f"오류: {e}\n\n"
                "확인할 것:\n"
                "1. .env에 GEMINI_API_KEY가 들어갔는지 확인\n"
                "2. GEMINI_MODEL 이름이 올바른지 확인\n"
                "3. Gemini API 무료 한도 또는 rate limit을 초과하지 않았는지 확인\n"
                "4. 인터넷 연결 상태 확인"
            )

    def call(self, prompt: str) -> str:
        return self.generate(prompt)

    def run(self, prompt: str) -> str:
        return self.generate(prompt)


def generate_response(prompt: str) -> str:
    """
    함수형 호출도 지원하기 위한 진입점.
    """
    provider = GeminiProvider()
    return provider.generate(prompt)