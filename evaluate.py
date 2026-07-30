"""Evaluation scorecard.

Measures four things and prints a summary:
  1. Tool reliability   - do the three tools return real data, and how fast?
  2. Memory recall      - does the vector store retrieve the right note by meaning?
  3. Planning accuracy  - are the correct tools chosen for a request? (needs LLM)
  4. End-to-end         - a full trip request: latency and tools used. (needs LLM)

Run with:  python evaluate.py
Parts 3 and 4 are skipped automatically if GROQ_API_KEY is not set.
"""

import time

from app import config
from app.tools import run_tool
from app.memory import LongTermMemory


def timed(fn):
    start = time.time()
    result = fn()
    return result, round(time.time() - start, 2)


def section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def test_tools():
    section("1. TOOL RELIABILITY")
    cases = [
        ("get_weather",  {"city": "Tokyo"}),
        ("web_search",   {"query": "best sushi in Tokyo", "max_results": 3}),
        ("wiki_research", {"city": "Paris", "interests": "museums"}),
    ]
    passed = 0
    for name, args in cases:
        result, secs = timed(lambda: run_tool(name, args))
        ok = "error" not in result
        passed += ok
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<14} {secs:>5}s   "
              f"{'returned data' if ok else result.get('error')}")
    print(f"  -> Tool success rate: {passed}/{len(cases)}")
    return passed, len(cases)


def test_memory():
    section("2. MEMORY RECALL")
    mem = LongTermMemory()
    user = "eval-user"
    for f in [
        "The user is vegetarian and avoids meat.",
        "The user prefers cheap budget hostels.",
        "The user loves art museums and galleries.",
    ]:
        mem.remember(user, f)

    checks = [
        ("What kind of food does the user eat?", "vegetarian"),
        ("What is the user's budget like?",       "budget"),
        ("What activities does the user enjoy?",  "museums"),
    ]
    passed = 0
    for query, expected_word in checks:
        top = mem.recall(user, query, k=1)
        hit = bool(top) and expected_word in top[0].lower()
        passed += hit
        got = top[0] if top else "(nothing)"
        print(f"  {'PASS' if hit else 'FAIL'}  Q: {query}\n        -> recalled: {got}")
    print(f"  -> Recall precision: {passed}/{len(checks)}")
    return passed, len(checks)


def test_planning():
    section("3. PLANNING ACCURACY")
    from app.planner import make_plan

    cases = [
        ("Plan a 2-day trip to Rome, I like history",  {"wiki_research"}),
        ("What's the weather like for my trip to London?", {"get_weather"}),
        ("Find me trendy new cafes in Berlin right now",   {"web_search"}),
        ("I want to visit somewhere nice", set()),  # ambiguous -> should ask
    ]
    passed = 0
    for message, expected_tools in cases:
        plan, secs = timed(lambda: make_plan(message, [], []))
        chosen = {s.get("tool") for s in plan["steps"]}
        ok = expected_tools.issubset(chosen) if expected_tools else plan["needs_clarification"]
        passed += ok
        print(f"  {'PASS' if ok else 'FAIL'}  {secs:>5}s  "
              f"'{message[:40]}...'  -> tools={chosen or 'ask user'}")
    print(f"  -> Planning accuracy: {passed}/{len(cases)}")
    return passed, len(cases)


def test_end_to_end():
    section("4. END-TO-END")
    from app.agent import TravelAgent
    agent = TravelAgent()

    msg = "Plan a 2-day trip to Kyoto. I'm vegetarian and love temples."
    result, secs = timed(lambda: agent.chat("eval-s", "eval-e2e", msg))
    print(f"  Request: {msg}")
    print(f"  Latency: {secs}s")
    print(f"  Tools used: {result['reasoning']['tools_used']}")
    print(f"  Itinerary length: {len(result['reply'])} characters")
    print("\n  --- First 400 chars of the itinerary ---")
    print("  " + result["reply"][:400].replace("\n", "\n  "))
    return 1, 1


if __name__ == "__main__":
    total_pass, total = 0, 0

    p, t = test_tools();   total_pass += p; total += t
    p, t = test_memory();  total_pass += p; total += t

    if config.llm_is_configured():
        p, t = test_planning(); total_pass += p; total += t
        test_end_to_end()
    else:
        section("3 & 4 SKIPPED")
        print("  No GROQ_API_KEY set; planning and end-to-end tests are skipped.")

    section(f"SCORECARD:  {total_pass}/{total} checks passed")
