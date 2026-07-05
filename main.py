from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import AI_PROVIDER
from core.command_parser import parse_command
from core.prompt_builder import build_prompt
from core.ai_client import generate_ai_response


app = FastAPI(
    title="CRENOBA Core Agent API",
    description="Provider-switchable AI Agent API for CRENOBA",
    version="0.6.0",
)


class AgentRequest(BaseModel):
    message: str


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    return {
        "message": "CRENOBA Core Agent API is running",
        "version": "0.6.0",
        "provider": AI_PROVIDER,
        "web_ui": "http://127.0.0.1:8000/static/index.html",
        "commands": [
            "/crenoba task",
            "/crenoba study",
            "/crenoba code",
            "/crenoba report",
            "/crenoba project",
            "/crenoba apollo",
            "/crenoba relay",
        ],
    }


@app.post("/agent")
def agent(req: AgentRequest):
    parsed = parse_command(req.message)

    command = parsed["command"]
    content = parsed["content"]

    agent_name, prompt = build_prompt(command, content)

    result = generate_ai_response(prompt)

    return {
        "command": command,
        "agent": agent_name,
        "provider": result["provider"],
        "source": result["source"],
        "model": result["model"],
        "output": result["output"],
        "error": result["error"],
    }