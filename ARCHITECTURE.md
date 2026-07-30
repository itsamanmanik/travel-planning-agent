# Architecture & Design Notes

## Overview

The agent handles one message in five stages, each in its own module:

```
User message
   │
   ▼
1. Recall     load conversation (short-term) + preferences (long-term)
2. Plan       LLM returns a JSON plan: which tools, or a clarifying question
3. Act        run the chosen tools (weather / web / wiki)
4. Synthesize LLM writes the 2-day itinerary from the gathered facts
5. Learn      store any new durable preferences
```

| Stage | Module |
| --- | --- |
| Recall | `memory.py` |
| Plan | `planner.py` |
| Act | `tools/` |
| Synthesize | `agent.py` + `llm.py` |
| Learn | `agent.py` + `memory.py` |

Keeping the stages separate makes the flow easy to follow and to test in
isolation.

## Why a custom loop instead of LangChain

The brief allowed either. I went with a small custom loop because the whole
decision flow fits in `agent.py` and can be read in a couple of minutes, it
pulls in fewer dependencies (simpler to install and deploy for free), and it's
straightforward to explain. The cost is writing a bit more glue myself, which
is a fair trade for the clarity.

## Planning

`planner.py` sends the LLM the user's message, recent conversation, and known
preferences, and asks for a JSON plan:

```json
{
  "thought": "User wants a Tokyo trip and is vegetarian",
  "needs_clarification": false,
  "clarifying_question": "",
  "steps": [
    {"tool": "wiki_research", "args": {"city": "Tokyo", "interests": "food"}},
    {"tool": "get_weather",   "args": {"city": "Tokyo"}}
  ]
}
```

This one step covers three requirements: it breaks the goal into sub-tasks,
chooses tools dynamically (a weather-only question won't trigger Wikipedia), and
asks a clarifying question instead of guessing when the city is missing. Groq's
`response_format={"type": "json_object"}` guarantees the output parses.

## Tools

Three tools, each free and keyless, each covering a distinct need:

- `get_weather` (Open-Meteo) — forecast, so the plan can favor indoor options on
  wet days.
- `web_search` (DuckDuckGo) — live info the model wouldn't know: current hours,
  new places, events.
- `wiki_research` (Wikipedia) — grounded facts about real attractions; the base
  for the multi-hop RAG.

Two design points keep this robust: every tool returns a dict and reports
failures as `{"error": ...}` rather than raising, so one dead endpoint can't
break a whole request; and tools are registered with a name + description in
`tools/__init__.py`, so adding a fourth tool is just a function plus a catalog
entry.

### Multi-hop RAG (`wiki_research`)

The second retrieval depends on the first:

```
Hop 1: search "tourist attractions in Kyoto" → ["Kinkaku-ji", "Fushimi Inari", ...]
Hop 2: fetch each attraction's Wikipedia summary (+ the city overview)
      → a grounded fact pack for the LLM
```

Because the itinerary is written from these summaries, it names real places with
real descriptions instead of guessing.

## Memory

Two kinds:

**Short-term** (`ShortTermMemory`) — the current conversation, kept in RAM per
`session_id`, capped to the last N messages. It's what makes follow-ups like
"make day 2 more relaxed" work. It clears on restart, which is what you want for
a transient conversation.

**Long-term** (`LongTermMemory`) — durable facts about the user (vegetarian,
budget, likes museums), stored in ChromaDB on disk. A vector store is used
because it searches by meaning: "what food does the user like?" retrieves "I am
vegetarian" even with no shared words. Each note is tagged with `user_id` so one
deployment can serve many users without mixing preferences.

Why ChromaDB over Pinecone/FAISS: Pinecone is a paid cloud service (breaks the
zero-cost rule); FAISS is free but only does the vector math and needs a
separate embedding model (a heavy `torch` install with no wheels for the very
new Python on this machine). ChromaDB is free, local, persists to disk, and
bundles a small embedding model, so it runs here with the least code. It's a
drop-in swap if a hosted store is wanted later.

After each reply, the agent asks the LLM to extract any *lasting* preference
from the message (ignoring one-off details like the city) and stores it. That's
how it gets to know a user over time.

## Interface

- `POST /chat` — send `{message, session_id, user_id}`, get `{reply, reasoning}`.
  The `reasoning` field exposes the plan's thought, the tools used, and the
  memories recalled, which is useful for demos and grading.
- `GET /` — a self-contained chat page that also shows those reasoning chips.
- `GET /memory/{user_id}` — inspect what's stored for a user.
- `GET /docs` — FastAPI's auto-generated API docs.

## Evaluation

`evaluate.py` scores four things: tool reliability (+latency), memory-recall
precision, planning accuracy (right tools per labeled request, and a clarifying
question when ambiguous), and an end-to-end run. It turns "it works" into
numbers.

## Deployment

The `Dockerfile` uses Python 3.12 for the widest wheel compatibility and runs on
any free host.

- Hugging Face Spaces: new Docker Space, upload the files, add `GROQ_API_KEY` as
  a Secret.
- Render: new Web Service, connect the repo, it detects the Dockerfile, add
  `GROQ_API_KEY`. The free tier sleeps when idle and wakes on the next request.

Long-term memory lives on the container disk; on free tiers that can reset on
redeploy. For permanent cross-deploy memory, attach a volume or point ChromaDB
at a hosted store — a one-line change in `config.py`.

## Limitations

- Free LLM tiers have rate limits — fine for demos, may need throttling under load.
- Live web/wiki calls add a few seconds of latency; that's the cost of using
  real data over guessing.
- No auth: `user_id` is trusted as-is; a real product would add login.
