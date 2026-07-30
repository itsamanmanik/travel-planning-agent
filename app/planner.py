"""Planning step.

Given the user's message, recent conversation, and known preferences, the
planner asks the LLM for a structured JSON plan: whether to ask a clarifying
question, and which tools to run with which arguments.
"""

import json

from . import llm
from .tools import TOOL_CATALOG

_TOOLS_AS_TEXT = json.dumps(TOOL_CATALOG, indent=2)

PLANNER_SYSTEM_PROMPT = f"""You are the planning brain of a travel-planning agent.
Your job is to look at the user's request and decide the next actions.

You can use these tools:
{_TOOLS_AS_TEXT}

Reply with ONLY a JSON object in this exact shape:
{{
  "thought": "one short sentence on your reasoning",
  "needs_clarification": true or false,
  "clarifying_question": "a question to ask the user, or empty string",
  "steps": [
     {{"tool": "tool_name", "args": {{ ... }} }}
  ]
}}

Rules:
- If the user has not given a city, set needs_clarification=true and ask for it.
- For a real 2-day trip plan, normally use wiki_research AND get_weather,
  and add web_search when up-to-date details (hours, events, food) would help.
- Only include tools you actually need. Keep "steps" empty if you just need
  to ask a clarifying question or chat.
- Respect any remembered user preferences (e.g. vegetarian, budget, pets).
"""


def make_plan(user_message: str, history: list[dict], memories: list[str]) -> dict:
    """Ask the LLM for a structured plan and normalise it to a safe shape."""

    memory_text = "\n".join(f"- {m}" for m in memories) if memories else "None yet."

    messages = [
        {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Known preferences about this user:\n{memory_text}\n\n"
            f"Recent conversation:\n{_format_history(history)}\n\n"
            f"New user message:\n{user_message}\n\n"
            "Produce the JSON plan now."
        )},
    ]

    plan = llm.chat_json(messages)

    return {
        "thought": plan.get("thought", ""),
        "needs_clarification": bool(plan.get("needs_clarification", False)),
        "clarifying_question": plan.get("clarifying_question", ""),
        "steps": plan.get("steps", []) or [],
    }


def _format_history(history: list[dict]) -> str:
    if not history:
        return "(none)"
    return "\n".join(f"{m['role']}: {m['content']}" for m in history)
