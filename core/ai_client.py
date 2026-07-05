from config import AI_PROVIDER
from providers import gemini_provider, openai_provider, mock_provider


def generate_ai_response(prompt: str):
    if AI_PROVIDER == "mock":
        return mock_provider.generate(prompt)

    if AI_PROVIDER == "gemini":
        return gemini_provider.generate(prompt)

    if AI_PROVIDER == "openai":
        return openai_provider.generate(prompt)

    return {
        "provider": AI_PROVIDER,
        "source": "failed",
        "model": None,
        "output": None,
        "error": f"Unsupported AI_PROVIDER: {AI_PROVIDER}",
    }