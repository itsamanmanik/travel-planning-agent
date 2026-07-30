"""Automated tests for the pieces that don't require the LLM key.

Run with:  pytest
"""

from app.tools import run_tool
from app.memory import ShortTermMemory, LongTermMemory


def test_weather_tool_returns_forecast():
    result = run_tool("get_weather", {"city": "Tokyo"})
    assert "error" not in result
    assert len(result["forecast"]) >= 1


def test_wiki_tool_is_multi_hop():
    result = run_tool("wiki_research", {"city": "Paris"})
    assert "error" not in result
    assert result["hops"] == 2
    assert len(result["attractions"]) >= 1


def test_short_term_memory_keeps_recent_messages():
    stm = ShortTermMemory(max_messages=4)
    for i in range(10):
        stm.add("s1", "user", f"message {i}")
    assert len(stm.get("s1")) == 4


def test_long_term_memory_recalls_by_meaning():
    ltm = LongTermMemory()
    ltm.remember("test-user", "The user is vegetarian.")
    top = ltm.recall("test-user", "what food do they eat", k=1)
    assert top and "vegetarian" in top[0].lower()
