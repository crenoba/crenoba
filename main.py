import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from core.ai_client import AIClient


APP_VERSION = "v0.9.4.1"

app = FastAPI(
    title="CRENOBA",
    description="CRENOBA Agent System",
    version=APP_VERSION,
)

client = AIClient()


class RelayRequest(BaseModel):
    prompt: str


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index():
    index_file = STATIC_DIR / "index.html"

    if index_file.exists():
        return FileResponse(str(index_file))

    return {
        "app": "CRENOBA",
        "version": APP_VERSION,
        "message": "static/index.html 파일을 찾을 수 없습니다.",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": "CRENOBA",
        "version": APP_VERSION,
    }


@app.post("/relay")
def relay(req: RelayRequest):
    start_time = time.perf_counter()

    result = client.generate(req.prompt)

    end_time = time.perf_counter()
    elapsed_sec = round(end_time - start_time, 2)

    return {
        "output": result.get("output", ""),
        "mode": result.get("mode", "general"),
        "agent": result.get("agent", "general"),
        "provider": result.get("provider", "unknown"),
        "model": result.get("model", "unknown"),
        "response_time_sec": elapsed_sec,
        "version": APP_VERSION,
    }