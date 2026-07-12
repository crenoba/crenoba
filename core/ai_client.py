from core.provider_router import ProviderRouter

from providers.mock_provider import MockProvider
from providers.ollama_provider import OllamaProvider


class AIClient:
    """
    CRENOBA AI Client

    역할:
    1. ProviderRouter로 Agent별 Provider / Model 결정
    2. 선택된 Provider 호출
    3. UI에 필요한 metadata 포함해서 반환

    반환 구조:
    {
        "output": "...",
        "mode": "code",
        "agent": "code",
        "provider": "ollama",
        "model": "qwen2.5-coder:7b-instruct",
        "version": "v0.9.6"
    }
    """

    def __init__(self):
        self.router = ProviderRouter()
        self.providers = self._load_providers()

    def _load_providers(self) -> dict:
        providers = {
            "mock": MockProvider(),
            "ollama": OllamaProvider(),
        }

        try:
            from providers.openrouter_provider import OpenRouterProvider
            providers["openrouter"] = OpenRouterProvider()
        except Exception:
            pass

        try:
            from providers.gemini_provider import GeminiProvider
            providers["gemini"] = GeminiProvider()
        except Exception:
            pass

        try:
            from providers.openai_provider import OpenAIProvider
            providers["openai"] = OpenAIProvider()
        except Exception:
            pass

        return providers

    def generate_response(
        self,
        prompt: str,
        mode: str | None = None,
        agent: str | None = None,
    ) -> dict:
        route = self.router.resolve(mode=mode, agent=agent)

        provider_name = route.provider
        provider = self.providers.get(provider_name)

        if provider is None:
            provider_name = "mock"
            provider = self.providers["mock"]

        output = self._call_provider(
            provider=provider,
            prompt=prompt,
            mode=route.mode,
            agent=route.agent,
            model=route.model,
        )

        return {
            "output": output,
            "mode": route.mode,
            "agent": route.agent,
            "provider": provider_name,
            "model": route.model,
            "version": route.version,
        }

    def generate(
        self,
        prompt: str,
        mode: str | None = None,
        agent: str | None = None,
    ) -> dict:
        return self.generate_response(
            prompt=prompt,
            mode=mode,
            agent=agent,
        )

    def _call_provider(
        self,
        provider,
        prompt: str,
        mode: str,
        agent: str,
        model: str,
    ) -> str:
        """
        Provider마다 generate_response 인자 구조가 조금 달라도
        최대한 호환되도록 호출한다.
        """

        try:
            result = provider.generate_response(
                prompt=prompt,
                mode=mode,
                agent=agent,
                model=model,
            )
        except TypeError:
            try:
                result = provider.generate_response(
                    prompt=prompt,
                    mode=mode,
                    agent=agent,
                )
            except TypeError:
                result = provider.generate_response(prompt)

        return self._normalize_provider_output(result)

    def _normalize_provider_output(self, result) -> str:
        if result is None:
            return "[CRENOBA Empty Response] Provider returned None."

        if isinstance(result, str):
            return result

        if isinstance(result, dict):
            if "output" in result:
                return str(result["output"])

            if "text" in result:
                return str(result["text"])

            if "content" in result:
                return str(result["content"])

            return str(result)

        return str(result)