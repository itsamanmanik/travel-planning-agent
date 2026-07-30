"""FastAPI application: REST API for the agent, plus the static chat UI.

Endpoints:
  GET  /              chat web UI
  POST /chat          send a message to the agent
  GET  /memory/{user} inspect stored preferences for a user
  GET  /health        status check

Run:   uvicorn app.main:app --reload
Docs:  http://localhost:8000/docs
"""

import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import config
from .agent import TravelAgent

app = FastAPI(title="Travel Planning AI Agent")

# One agent instance is created at startup and reused for every request.
agent = TravelAgent()

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default-session"   # groups one conversation
    user_id: str = "default-user"         # identifies a user across sessions


@app.get("/health")
def health():
    return {"status": "ok", "llm_configured": config.llm_is_configured()}


@app.post("/chat")
def chat(req: ChatRequest):
    if not config.llm_is_configured():
        return {
            "reply": "The AI brain is not configured yet. Add a GROQ_API_KEY "
                     "to your .env file (free key at https://console.groq.com).",
            "reasoning": {"thought": "", "tools_used": [], "memories_recalled": []},
        }
    return agent.chat(req.session_id, req.user_id, req.message)


@app.get("/memory/{user_id}")
def memory(user_id: str):
    return {"user_id": user_id, "preferences": agent.long_term.all_for_user(user_id)}


@app.get("/")
def home():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
