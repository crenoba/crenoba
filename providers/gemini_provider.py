import google.generativeai as genai

from config import (
    GEMINI_API_KEY,
    GEMINI_PRIMARY_MODEL,
    GEMINI_FALLBACK_MODEL,
)


if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def call_gemini(model_name: str, prompt: str):
    try:
        if not GEMINI_API_KEY:
            return None, "GEMINI_API_KEY is missing"

        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)

        output = getattr(response, "text", None)

        if not output:
            return None, "Empty response from Gemini"

        return output, None

    except Exception as e:
        return None, str(e)


def generate(prompt: str):
    result, error = call_gemini(GEMINI_PRIMARY_MODEL, prompt)

    if result:
        return {
            "provider": "gemini",
            "source": "primary",
            "model": GEMINI_PRIMARY_MODEL,
            "output": result,
            "error": None,
        }

    fallback_result, fallback_error = call_gemini(GEMINI_FALLBACK_MODEL, prompt)

    if fallback_result:
        return {
            "provider": "gemini",
            "source": "fallback",
            "model": GEMINI_FALLBACK_MODEL,
            "output": fallback_result,
            "error": error,
        }

    return {
        "provider": "gemini",
        "source": "failed",
        "model": None,
        "output": None,
        "error": {
            "primary_error": error,
            "fallback_error": fallback_error,
        },
    }