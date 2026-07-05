from core.provider_router import ProviderRouter, RouteResult


class AIClient:
    """
    CRENOBA AI Client
    ProviderRouter가 결정한 Provider / Model을 실제 Provider에 전달한다.
    """

    def __init__(self):
        self.router = ProviderRouter()

    def generate(self, user_input: str) -> dict:
        route = self.router.route(user_input)
        provider = self._load_provider(route.provider)

        try:
            output = provider.generate(
                user_input,
                model_override=route.model,
                agent=route.agent,
                mode=route.mode,
            )
        except TypeError:
            output = provider.generate(user_input)

        return {
            "output": output,
            "mode": route.mode,
            "agent": route.agent,
            "provider": route.provider,
            "model": route.model,
        }

    def _load_provider(self, provider_name: str):
        provider_name = provider_name.lower().strip()

        if provider_name == "mock":
            from providers.mock_provider import MockProvider
            return MockProvider()

        if provider_name == "gemini":
            from providers.gemini_provider import GeminiProvider
            return GeminiProvider()

        if provider_name == "openrouter":
            from providers.openrouter_provider import OpenRouterProvider
            return OpenRouterProvider()

        if provider_name == "ollama":
            from providers.ollama_provider import OllamaProvider
            return OllamaProvider()

        if provider_name == "openai":
            from providers.openai_provider import OpenAIProvider
            return OpenAIProvider()

        from providers.mock_provider import MockProvider
        return MockProvider()


def generate_response(user_input: str) -> dict:
    client = AIClient()
    return client.generate(user_input)