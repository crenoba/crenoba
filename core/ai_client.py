# core/ai_client.py

"""
CRENOBA AI Client

역할:
- main.py에서 선택한 AI_PROVIDER 값에 따라 provider를 연결한다.
- mock, gemini, openai provider를 같은 방식으로 호출할 수 있게 맞춘다.
- main.py에서는 get_ai_client(provider).generate(prompt) 형태로 사용한다.
"""


class ProviderFunctionAdapter:
    """
    함수 기반 provider를 class처럼 사용할 수 있게 감싸는 adapter.
    """

    def __init__(self, generate_func):
        self.generate_func = generate_func

    def generate(self, prompt: str) -> str:
        return self.generate_func(prompt)

    def call(self, prompt: str) -> str:
        return self.generate(prompt)

    def run(self, prompt: str) -> str:
        return self.generate(prompt)


class ProviderObjectAdapter:
    """
    provider 객체가 generate/call/run 중 어떤 메서드를 가지고 있어도
    main.py에서는 generate()로 호출할 수 있게 맞추는 adapter.
    """

    def __init__(self, provider_object):
        self.provider_object = provider_object

    def generate(self, prompt: str) -> str:
        if hasattr(self.provider_object, "generate"):
            return self.provider_object.generate(prompt)

        if hasattr(self.provider_object, "call"):
            return self.provider_object.call(prompt)

        if hasattr(self.provider_object, "run"):
            return self.provider_object.run(prompt)

        raise AttributeError("Provider object has no generate, call, or run method.")

    def call(self, prompt: str) -> str:
        return self.generate(prompt)

    def run(self, prompt: str) -> str:
        return self.generate(prompt)


def get_mock_client():
    """
    Mock Provider 연결.
    현재 CRENOBA v0.7 개발 기본 provider.
    """
    try:
        from providers.mock_provider import MockProvider

        return ProviderObjectAdapter(MockProvider())
    except Exception:
        from providers.mock_provider import generate_response

        return ProviderFunctionAdapter(generate_response)


def get_gemini_client():
    """
    Gemini Provider 연결.
    현재는 기존 gemini_provider.py 구조를 최대한 유지하면서 연결한다.
    """
    try:
        from providers.gemini_provider import GeminiProvider

        return ProviderObjectAdapter(GeminiProvider())
    except Exception:
        try:
            from providers.gemini_provider import generate_response

            return ProviderFunctionAdapter(generate_response)
        except Exception:
            try:
                from providers.gemini_provider import call_gemini

                return ProviderFunctionAdapter(call_gemini)
            except Exception as e:
                raise ImportError(f"Gemini provider could not be loaded: {e}")


def get_openai_client():
    """
    OpenAI Provider 연결.
    현재는 기존 openai_provider.py 구조를 최대한 유지하면서 연결한다.
    """
    try:
        from providers.openai_provider import OpenAIProvider

        return ProviderObjectAdapter(OpenAIProvider())
    except Exception:
        try:
            from providers.openai_provider import generate_response

            return ProviderFunctionAdapter(generate_response)
        except Exception:
            try:
                from providers.openai_provider import call_openai

                return ProviderFunctionAdapter(call_openai)
            except Exception as e:
                raise ImportError(f"OpenAI provider could not be loaded: {e}")


def get_ai_client(provider_name: str = "mock"):
    """
    main.py에서 호출하는 핵심 함수.

    사용 예:
    ai_client = get_ai_client("mock")
    output = ai_client.generate(prompt)
    """
    provider = (provider_name or "mock").lower().strip()

    if provider == "mock":
        return get_mock_client()

    if provider == "gemini":
        return get_gemini_client()

    if provider == "openai":
        return get_openai_client()

    return get_mock_client()