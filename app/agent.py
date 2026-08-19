"""TravelAgent: orchestrates one request end to end.

Each message flows through five stages: recall memory, plan the tools, run the
tools, synthesise the itinerary, and learn any new preferences.
"""

from . import llm
from .memory import ShortTermMemory, LongTermMemory
from .planner import make_plan
from .tools import run_tool


ANSWER_SYSTEM_PROMPT = """You are a friendly, expert travel planner.
Using ONLY the facts provided (tool results + user preferences), write a
clear, personalized 2-DAY itinerary.

Format:
- A one-line intro.
- "Day 1" and "Day 2", each with Morning / Afternoon / Evening.
- Concrete place names from the research. Note weather-based tips.
- Respect the user's preferences (diet, budget, pets, pace, etc.).
- End with 2-3 quick practical tips.
Keep it enthusiastic but concise. Do not invent facts you were not given.
"""

MEMORY_EXTRACT_PROMPT = """From the user's message, extract any LASTING personal
travel preferences worth remembering for future trips (diet, budget level,
interests, pace, mobility, pets, likes/dislikes).

Reply with ONLY JSON: {"preferences": ["short note", ...]}
If there are none, reply {"preferences": []}.
Do NOT include one-off details like the specific city or dates."""


class TravelAgent:
    def __init__(self):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()

    def chat(self, session_id: str, user_id: str, message: str) -> dict:
        """Handle one user message; return the reply and a summary of the reasoning."""

        # 1. Recall short-term (conversation) and long-term (preferences) memory.
        history = self.short_term.get(session_id)
        memories = self.long_term.recall(user_id, message)

        # 2. Plan: decide whether to clarify, and which tools to run.
        plan = make_plan(message, history, memories)

        # Ask instead of guessing when the request is ambiguous.
        # Still run the learn step so preferences stated alongside a vague request are saved.
        if plan["needs_clarification"] and plan["clarifying_question"]:
            reply = plan["clarifying_question"]
            self._learn_preferences(user_id, message)
            self._save_turn(session_id, message, reply)
            return self._response(reply, plan, tools_used=[], memories=memories)

        # 3. Act: run each planned tool.
        tool_outputs = []
        for step in plan["steps"]:
            name = step.get("tool")
            args = step.get("args", {})
            result = run_tool(name, args)
            tool_outputs.append({"tool": name, "args": args, "result": result})

        # 4. Synthesise the final itinerary from the gathered facts.
        reply = self._write_answer(message, history, memories, tool_outputs)

        # 5. Learn: persist any new durable preferences.
        self._learn_preferences(user_id, message)

        self._save_turn(session_id, message, reply)

        tools_used = [t["tool"] for t in tool_outputs]
        return self._response(reply, plan, tools_used, memories)

    def _write_answer(self, message, history, memories, tool_outputs) -> str:
        facts = self._format_facts(memories, tool_outputs)
        messages = [
            {"role": "system", "content": ANSWER_SYSTEM_PROMPT},
            *history,
            {"role": "user", "content": (
                f"User request: {message}\n\n"
                f"Facts you may use:\n{facts}"
            )},
        ]
        return llm.chat(messages)

    def _learn_preferences(self, user_id: str, message: str) -> None:
        # Learning is best-effort and must never break the main reply.
        try:
            result = llm.chat_json([
                {"role": "system", "content": MEMORY_EXTRACT_PROMPT},
                {"role": "user", "content": message},
            ])
            for pref in result.get("preferences", []):
                if pref and pref.strip():
                    self.long_term.remember(user_id, pref.strip())
        except Exception:
            pass

    def _save_turn(self, session_id, user_message, agent_reply) -> None:
        self.short_term.add(session_id, "user", user_message)
        self.short_term.add(session_id, "assistant", agent_reply)

    @staticmethod
    def _format_facts(memories, tool_outputs) -> str:
        import json
        parts = []
        if memories:
            parts.append("User preferences:\n" +
                         "\n".join(f"- {m}" for m in memories))
        for out in tool_outputs:
            parts.append(f"[{out['tool']}] result:\n"
                         f"{json.dumps(out['result'], ensure_ascii=False)[:2500]}")
        return "\n\n".join(parts) if parts else "No extra facts gathered."

    @staticmethod
    def _response(reply, plan, tools_used, memories) -> dict:
        return {
            "reply": reply,
            "reasoning": {
                "thought": plan.get("thought", ""),
                "tools_used": tools_used,
                "memories_recalled": memories,
            },
        }
