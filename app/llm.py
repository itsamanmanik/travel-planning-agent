"""Groq client wrapper. Exposes text and JSON chat helpers used across the app."""

import json
from groq import Groq

from . import config

_client = Groq(api_key=config.GROQ_API_KEY) if config.llm_is_configured() else None


def _require_client():
    if _client is None:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to a .env file "
            "(get a free key at https://console.groq.com)."
        )


def chat(messages: list[dict], temperature: float = 0.6) -> str:
    """Return the model's plain-text reply for the given messages."""
    _require_client()
    response = _client.chat.completions.create(
        model=config.MODEL_NAME,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def chat_json(messages: list[dict], temperature: float = 0.2) -> dict:
    """Return the model's reply parsed as JSON. Used for structured planning."""
    _require_client()
    response = _client.chat.completions.create(
        model=config.MODEL_NAME,
        messages=messages,
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        return {}
