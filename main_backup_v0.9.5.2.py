import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import APP_NAME, APP_VERSION
from core.ai_client import AIClient
from core.command_parser import parse_command


# =========================
# APP INIT
# =========================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
)

ai_client = AIClient()


# =========================
# STATIC FILES
# =========================

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# =========================
# REQUEST MODEL
# =========================

class RelayRequest(BaseModel):
    prompt: str


# =========================
# ROUTES
# =========================

@app.get("/")
def read_index():
    index_path = STATIC_DIR / "index.html"

    if index_path.exists():
        return FileResponse(str(index_path))

    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "message": "CRENOBA backend is running.",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION,
    }


@app.post("/relay")
def relay(req: RelayRequest):
    start_time = time.perf_counter()

    raw_prompt = req.prompt.strip()
    parsed = parse_command(raw_prompt)

    agent_prompt = parsed["content"]
    mode = parsed["mode"]
    agent = parsed["agent"]

    if not agent_prompt:
        agent_prompt = raw_prompt

    try:
        result = ai_client.generate_response(
            prompt=agent_prompt,
            mode=mode,
            agent=agent,
        )

        response_time_sec = round(time.perf_counter() - start_time, 2)

        return {
            "output": result.get("output", ""),
            "mode": result.get("mode", mode),
            "agent": result.get("agent", agent),
            "provider": result.get("provider", "unknown"),
            "model": result.get("model", "unknown"),
            "version": result.get("version", APP_VERSION),
            "response_time_sec": response_time_sec,
        }

    except Exception as e:
        response_time_sec = round(time.perf_counter() - start_time, 2)

        return {
            "output": (
                "[CRENOBA Backend Error]\n\n"
                "요청 처리 중 오류가 발생했습니다.\n\n"
                f"Error: {str(e)}"
            ),
            "mode": mode,
            "agent": agent,
            "provider": "error",
            "model": "error",
            "version": APP_VERSION,
            "response_time_sec": response_time_sec,
        }


@app.post("/api/relay")
def api_relay(req: RelayRequest):
    return relay(req)