import os
from dotenv import load_dotenv

load_dotenv()

AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

GEMINI_PRIMARY_MODEL = os.getenv(
    "GEMINI_PRIMARY_MODEL",
    "models/gemini-2.5-flash"
)

GEMINI_FALLBACK_MODEL = os.getenv(
    "GEMINI_FALLBACK_MODEL",
    "models/gemini-2.0-flash-lite"
)

OPENAI_PRIMARY_MODEL = os.getenv(
    "OPENAI_PRIMARY_MODEL",
    "gpt-5.4"
)

OPENAI_FALLBACK_MODEL = os.getenv(
    "OPENAI_FALLBACK_MODEL",
    "gpt-5.4"
)