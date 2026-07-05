# main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import AI_PROVIDER
from core.command_parser import parse_command
from core.prompt_builder import build_prompt
from core.ai_client import get_ai_client


app = FastAPI(title="CRENOBA Core Agent")


class AgentRequest(BaseModel):
    prompt: str


@app.post("/relay")
def relay(req: AgentRequest):
    parsed = parse_command(req.prompt)
    mode = parsed.get("mode", "general")

    prompt = build_prompt(req.prompt, mode)
    ai_client = get_ai_client(AI_PROVIDER)
    output = ai_client.generate(prompt)

    return {
        "provider": AI_PROVIDER,
        "mode": mode,
        "output": output,
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "provider": AI_PROVIDER,
    }


app.mount("/", StaticFiles(directory="static", html=True), name="static")