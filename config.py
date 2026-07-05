# config.py

"""
CRENOBA Config

역할:
- .env 파일에서 provider와 API 설정을 읽는다.
- 실제 비밀키는 .env에만 저장하고 GitHub에는 올리지 않는다.
"""

import os
from dotenv import load_dotenv


load_dotenv()


AI_PROVIDER = os.getenv("AI_PROVIDER", "mock").lower().strip()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite").strip()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free").strip()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()