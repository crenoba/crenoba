import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class RouteResult:
    mode: str
    agent: str
    provider: str
    model: str


class ProviderRouter:
    """
    CRENOBA v0.9.4
    Agent별 Provider / Model 자동 라우팅 담당
    """

    def __init__(self):
        self.provider_mode = os.getenv("AI_PROVIDER_MODE", "auto").lower().strip()

    def route(self, user_input: str) -> RouteResult:
        agent = self._detect_agent(user_input)
        mode = agent

        if self.provider_mode == "manual":
            provider = os.getenv("AI_PROVIDER", "ollama").lower().strip()
            model = self._get_model_for_provider(provider, "DEFAULT")
        else:
            provider = self._get_agent_provider(agent)
            model = self._get_agent_model(agent, provider)

        return RouteResult(
            mode=mode,
            agent=agent,
            provider=provider,
            model=model,
        )

    def _detect_agent(self, user_input: str) -> str:
        text = (user_input or "").strip().lower()

        if not text:
            return "general"

        first_line = text.splitlines()[0].strip()

        command_map = {
            "/crenoba code": "code",
            "/code": "code",

            "/crenoba task": "task",
            "/task": "task",

            "/crenoba study": "study",
            "/study": "study",

            "/crenoba report": "report",
            "/report": "report",

            "/crenoba project": "project",
            "/project": "project",

            "/crenoba apollo": "apollo",
            "/apollo": "apollo",

            "/crenoba relay": "relay",
            "/relay": "relay",
        }

        for command, agent in command_map.items():
            if first_line.startswith(command):
                return agent

        return "general"

    def _get_agent_provider(self, agent: str) -> str:
        agent_key = f"{agent.upper()}_PROVIDER"

        return os.getenv(
            agent_key,
            os.getenv("DEFAULT_PROVIDER", "ollama")
        ).lower().strip()

    def _get_agent_model(self, agent: str, provider: str) -> str:
        agent_upper = agent.upper()
        provider_upper = provider.upper()

        candidates = [
            f"{agent_upper}_{provider_upper}_MODEL",
            f"{agent_upper}_MODEL",
            f"DEFAULT_{provider_upper}_MODEL",
            "DEFAULT_MODEL",
        ]

        for key in candidates:
            value = os.getenv(key)
            if value:
                return value.strip()

        return self._get_model_for_provider(provider, "DEFAULT")

    def _get_model_for_provider(self, provider: str, prefix: str = "DEFAULT") -> str:
        provider = provider.lower().strip()

        if provider == "ollama":
            return os.getenv(
                f"{prefix}_OLLAMA_MODEL",
                os.getenv("OLLAMA_MODEL", "qwen3:14b")
            )

        if provider == "openrouter":
            return os.getenv(
                f"{prefix}_OPENROUTER_MODEL",
                os.getenv("OPENROUTER_MODEL", "openrouter/free")
            )

        if provider == "gemini":
            return os.getenv(
                f"{prefix}_GEMINI_MODEL",
                os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
            )

        if provider == "openai":
            return os.getenv(
                f"{prefix}_OPENAI_MODEL",
                os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            )

        if provider == "mock":
            return "mock-model"

        return "unknown-model"