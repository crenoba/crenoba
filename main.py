from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()

from core.agent_loop import ComputerAgent
from core.computer_command import ComputerCommandAgent
from core.ai_client import AIClient
from core.tool_router import ToolRouter


APP_VERSION = "v0.10.1"

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"

workspace_from_env = os.getenv("CRENOBA_WORKSPACE", "").strip()
WORKSPACE_ROOT = (
    Path(workspace_from_env).expanduser().resolve()
    if workspace_from_env
    else BASE_DIR.resolve()
)

app = FastAPI(
    title="CRENOBA",
    description="CRENOBA Agent System",
    version=APP_VERSION,
)

client = AIClient()
tool_router = ToolRouter(
    workspace_root=WORKSPACE_ROOT,
    log_file=DATA_DIR / "action_logs.jsonl",
)
computer_agent = ComputerAgent(tool_router)
computer_command_agent = ComputerCommandAgent(tool_router)


class RelayRequest(BaseModel):
    prompt: str


class ComputerChatRequest(BaseModel):
    prompt: str = Field(min_length=1)
    cwd: str = "."


class ToolExecutionRequest(BaseModel):
    tool: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)
    approved: bool = False


class ProjectInspectionRequest(BaseModel):
    cwd: str = "."


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
        "workspace": str(WORKSPACE_ROOT),
        "computer_agent": "read_only",
    }


@app.post("/relay")
def relay(req: RelayRequest):
    start_time = time.perf_counter()
    result = client.generate(req.prompt)
    end_time = time.perf_counter()
    response_time_sec = round(end_time - start_time, 2)

    return {
        "output": result.get("output", ""),
        "mode": result.get("mode", "general"),
        "agent": result.get("agent", "general"),
        "provider": result.get("provider", "unknown"),
        "model": result.get("model", "unknown"),
        "response_time_sec": response_time_sec,
        "version": APP_VERSION,
    }


@app.post("/computer/chat")
def computer_chat(req: ComputerChatRequest):
    result = computer_command_agent.run(prompt=req.prompt, cwd=req.cwd)
    return {**result, "version": APP_VERSION}


@app.get("/computer/tools")
def computer_tools():
    return {
        "mode": "computer",
        "workspace": str(WORKSPACE_ROOT),
        "tools": tool_router.tools(),
        "version": APP_VERSION,
    }


@app.post("/computer/execute")
def computer_execute(req: ToolExecutionRequest):
    result = tool_router.execute(
        tool_name=req.tool,
        arguments=req.arguments,
        approved=req.approved,
    )
    return {**result, "version": APP_VERSION}


@app.post("/computer/inspect")
def computer_inspect(req: ProjectInspectionRequest):
    result = computer_agent.inspect_project(cwd=req.cwd)
    return {
        **result,
        "workspace": str(WORKSPACE_ROOT),
        "version": APP_VERSION,
    }
