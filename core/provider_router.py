from dataclasses import dataclass

from config import (
    APP_VERSION,
    get_model_for_agent,
    get_provider_for_agent,
    normalize_agent,
    normalize_provider,
)


@dataclass
class RouteResult:
    mode: str
    agent: str
    provider: str
    model: str
    version: str

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "agent": self.agent,
            "provider": self.provider,
            "model": self.model,
            "version": self.version,
        }


class ProviderRouter:
    """
    CRENOBA v0.9.6 Provider Router

    역할:
    - /crenoba code  → Code Agent 감지
    - /crenoba apollo → Apollo Agent 감지
    - Agent별 Provider 선택
    - Agent별 Model 선택

    .env 예:
    CODE_PROVIDER=ollama
    CODE_OLLAMA_MODEL=qwen2.5-coder:7b-instruct

    APOLLO_PROVIDER=ollama
    APOLLO_OLLAMA_MODEL=qwen2.5-coder:7b-instruct
    """

    def resolve(self, mode: str | None = None, agent: str | None = None) -> RouteResult:
        resolved_agent = self._resolve_agent(mode=mode, agent=agent)
        resolved_mode = self._resolve_mode(mode=mode, agent=resolved_agent)

        provider = get_provider_for_agent(resolved_agent)
        provider = normalize_provider(provider)

        model = get_model_for_agent(resolved_agent, provider)

        return RouteResult(
            mode=resolved_mode,
            agent=resolved_agent,
            provider=provider,
            model=model,
            version=APP_VERSION,
        )

    def _resolve_agent(self, mode: str | None, agent: str | None) -> str:
        if agent:
            return normalize_agent(agent)

        if mode:
            return normalize_agent(mode)

        return "general"

    def _resolve_mode(self, mode: str | None, agent: str) -> str:
        if mode:
            return normalize_agent(mode)

        return normalize_agent(agent)