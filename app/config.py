"""Application configuration, loaded from environment variables (.env)."""

import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM (Groq) ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")

# --- Long-term memory (ChromaDB) persistence directory ---
CHROMA_DIR = os.getenv("CHROMA_DIR", "./data/chroma")

# --- Short-term memory: how many recent messages to keep as context ---
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "10"))


def llm_is_configured() -> bool:
    return bool(GROQ_API_KEY)
