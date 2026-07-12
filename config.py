import os
from dotenv import load_dotenv

# =========================
# ENV LOAD
# =========================

load_dotenv()


# =========================
# APP INFO
# =========================

APP_NAME = "CRENOBA"
APP_VERSION = "v0.9.6"


# =========================
# BASIC PROVIDER CONFIG
# =========================

AI_PROVIDER_MODE = os.getenv("AI_PROVIDER_MODE", "auto").strip().lower()
AI_PROVIDER = os.getenv("AI_PROVIDER", "mock").strip().lower()

DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", AI_PROVIDER).strip().lower()


# =========================
# OLLAMA CONFIG
# =========================

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:14b").strip()
DEFAULT_OLLAMA_MODEL = os.getenv("DEFAULT_OLLAMA_MODEL", OLLAMA_MODEL).strip()


# =========================
# OPENROUTER CONFIG
# =========================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free").strip()
DEFAULT_OPENROUTER_MODEL = os.getenv(
    "DEFAULT_OPENROUTER_MODEL",
    OPENROUTER_MODEL
).strip()


# =========================
# GEMINI CONFIG
# =========================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite").strip()
DEFAULT_GEMINI_MODEL = os.getenv("DEFAULT_GEMINI_MODEL", GEMINI_MODEL).strip()


# =========================
# OPENAI CONFIG
# =========================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
DEFAULT_OPENAI_MODEL = os.getenv("DEFAULT_OPENAI_MODEL", OPENAI_MODEL).strip()


# =========================
# AGENT LIST
# =========================

SUPPORTED_AGENTS = {
    "task",
    "study",
    "code",
    "report",
    "project",
    "apollo",
    "relay",
    "general",
}


# =========================
# HELPER FUNCTIONS
# =========================

def normalize_agent(agent: str | None) -> str:
    if not agent:
        return "general"

    cleaned = str(agent).strip().lower()

    if cleaned in SUPPORTED_AGENTS:
        return cleaned

    return "general"


def normalize_provider(provider: str | None) -> str:
    if not provider:
        return DEFAULT_PROVIDER or "mock"

    return str(provider).strip().lower()


def get_env_value(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def get_provider_for_agent(agent: str | None) -> str:
    """
    Agent별 Provider를 .env에서 읽는다.

    예:
    CODE_PROVIDER=ollama
    APOLLO_PROVIDER=ollama
    REPORT_PROVIDER=openrouter
    """

    normalized_agent = normalize_agent(agent)
    env_key = f"{normalized_agent.upper()}_PROVIDER"

    provider = os.getenv(env_key, "").strip().lower()

    if provider:
        return provider

    if normalized_agent == "general":
        return DEFAULT_PROVIDER or AI_PROVIDER or "mock"

    return DEFAULT_PROVIDER or AI_PROVIDER or "mock"


def get_default_model_for_provider(provider: str) -> str:
    normalized_provider = normalize_provider(provider)

    if normalized_provider == "ollama":
        return DEFAULT_OLLAMA_MODEL or OLLAMA_MODEL

    if normalized_provider == "openrouter":
        return DEFAULT_OPENROUTER_MODEL or OPENROUTER_MODEL

    if normalized_provider == "gemini":
        return DEFAULT_GEMINI_MODEL or GEMINI_MODEL

    if normalized_provider == "openai":
        return DEFAULT_OPENAI_MODEL or OPENAI_MODEL

    return "mock-model"


def get_model_for_agent(agent: str | None, provider: str | None) -> str:
    """
    Agent별 Model을 .env에서 읽는다.

    예:
    CODE_OLLAMA_MODEL=qwen2.5-coder:7b-instruct
    APOLLO_OLLAMA_MODEL=qwen2.5-coder:7b-instruct
    TASK_OLLAMA_MODEL=qwen3:14b
    """

    normalized_agent = normalize_agent(agent)
    normalized_provider = normalize_provider(provider)

    env_key = f"{normalized_agent.upper()}_{normalized_provider.upper()}_MODEL"
    agent_model = os.getenv(env_key, "").strip()

    if agent_model:
        return agent_model

    return get_default_model_for_provider(normalized_provider)