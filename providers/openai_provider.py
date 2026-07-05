from openai import OpenAI

from config import (
    OPENAI_API_KEY,
    OPENAI_PRIMARY_MODEL,
    OPENAI_FALLBACK_MODEL,
)


client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def call_openai(model_name: str, prompt: str):
    try:
        if not OPENAI_API_KEY or client is None:
            return None, "OPENAI_API_KEY is missing"

        response = client.responses.create(
            model=model_name,
            input=prompt,
        )

        output = getattr(response, "output_text", None)

        if not output:
            return None, "Empty response from OpenAI"

        return output, None

    except Exception as e:
        return None, str(e)


def generate(prompt: str):
    result, error = call_openai(OPENAI_PRIMARY_MODEL, prompt)

    if result:
        return {
            "provider": "openai",
            "source": "primary",
            "model": OPENAI_PRIMARY_MODEL,
            "output": result,
            "error": None,
        }

    fallback_result, fallback_error = call_openai(OPENAI_FALLBACK_MODEL, prompt)

    if fallback_result:
        return {
            "provider": "openai",
            "source": "fallback",
            "model": OPENAI_FALLBACK_MODEL,
            "output": fallback_result,
            "error": error,
        }

    return {
        "provider": "openai",
        "source": "failed",
        "model": None,
        "output": None,
        "error": {
            "primary_error": error,
            "fallback_error": fallback_error,
        },
    }