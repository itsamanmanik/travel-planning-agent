"""Scripted demo covering the main features.

  Message 1: a full 2-day trip request (tools + planning + RAG + itinerary).
  Message 2: an ambiguous request (the agent asks for clarification).
  Message 3: a new session for the same user (long-term memory across sessions).

Run with:  python demo.py
"""

from app.agent import TravelAgent

agent = TravelAgent()
USER = "demo-user-carlos"


def show(title, session, message):
    print("\n" + "#" * 64)
    print(f"# {title}")
    print("#" * 64)
    print(f"USER: {message}\n")
    result = agent.chat(session, USER, message)
    print(f"AGENT: {result['reply']}\n")
    r = result["reasoning"]
    print(f"[thought]   {r['thought']}")
    print(f"[tools]     {r['tools_used']}")
    print(f"[memory]    {r['memories_recalled']}")


show("MESSAGE 1  -  Full 2-day trip (learns preferences)",
     "session-A",
     "Plan a 2-day trip to Kyoto. I'm vegetarian and I love old temples.")

show("MESSAGE 2  -  Ambiguous request (asks for clarification)",
     "session-A",
     "Actually, plan me another trip somewhere fun.")

show("MESSAGE 3  -  New session: cross-session memory",
     "session-B",
     "Plan a single day in Osaka for me.")

print("\n" + "=" * 64)
print("In message 3 (a new session) the agent still knows the user is")
print("vegetarian, recalled from the ChromaDB long-term memory.")
print("=" * 64)
