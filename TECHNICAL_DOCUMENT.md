# Travel Planning AI Agent — Technical Document

**Live demo:** https://travel-planning-agent-abj1.onrender.com
**Source code:** https://github.com/itsamanmanik/travel-planning-agent

An AI agent that plans a personalized 2-day trip to any city. It selects tools
on its own, remembers user preferences across sessions using a vector database,
and grounds its suggestions in real data (weather, Wikipedia, live web). It runs
entirely on free services.

---

## 1. Architecture

The agent processes each message in five stages, each isolated in its own module:

```
User message
   │
   ▼
1. Recall     load conversation (short-term) + preferences (long-term)
2. Plan       the LLM returns a JSON plan: which tools, or a clarifying question
3. Act        run the chosen tools (weather / web / wiki)
4. Synthesize the LLM writes the 2-day itinerary from the gathered facts
5. Learn      store any new durable preference for future sessions
```

| Stage | Module |
| --- | --- |
| Recall | `app/memory.py` |
| Plan | `app/planner.py` |
| Act | `app/tools/` |
| Synthesize | `app/agent.py` + `app/llm.py` |
| Learn | `app/agent.py` + `app/memory.py` |

`app/main.py` is the web layer (FastAPI): it exposes the REST API and serves the
chat UI. Only `app/llm.py` talks to the LLM provider, so the model is a one-file
swap.

**Planning / reasoning.** `planner.py` sends the message, recent conversation,
and known preferences to the LLM and asks for a JSON plan, e.g.:

```json
{
  "thought": "User gave a city and interests, so research and weather are needed",
  "needs_clarification": false,
  "steps": [
    {"tool": "wiki_research", "args": {"city": "Jaipur", "interests": "forts"}},
    {"tool": "get_weather",   "args": {"city": "Jaipur"}}
  ]
}
```

This one step breaks the goal into sub-tasks, chooses tools dynamically, and asks
a clarifying question instead of guessing when the city is missing.

**Multi-hop RAG.** The `wiki_research` tool retrieves in two dependent hops:
hop 1 resolves the city to its top attraction page titles; hop 2 fetches a real
summary for each. The itinerary is written from those summaries, so it names real
places instead of hallucinating.

**Memory.**
- *Short-term* (`ShortTermMemory`): the current conversation, in RAM per session,
  capped to the last N messages.
- *Long-term* (`LongTermMemory`): durable user preferences stored in a ChromaDB
  vector collection on disk. Retrieval is by semantic similarity, so "what food
  does the user like?" recalls "I am vegetarian" despite no shared words. Each
  note is tagged with a `user_id` so one deployment serves many users.

---

## 2. Tools used

The agent has three tools, each free and keyless, each covering a distinct need.

| Tool | Source | Purpose |
| --- | --- | --- |
| `get_weather` | Open-Meteo | Multi-day forecast → indoor vs outdoor planning |
| `web_search` | DuckDuckGo (`ddgs`) | Live info: current hours, events, restaurants |
| `wiki_research` | Wikipedia API | Grounded facts about real attractions (multi-hop RAG) |

Tools are registered with a name + description in `app/tools/__init__.py`; the
planner reads those descriptions to choose. Every tool returns a dict and reports
failures as `{"error": ...}`, so one failing source never breaks a request.

### Full technology stack (all free)

| Layer | Choice |
| --- | --- |
| LLM | Groq — GPT OSS 120B (free API key, no card) |
| Vector DB | ChromaDB (local, on disk, bundled embeddings) |
| Web search | DuckDuckGo via `ddgs` |
| Weather | Open-Meteo |
| Attractions | Wikipedia API |
| API / server | FastAPI + Uvicorn |
| Deployment | Docker on Render (free tier) |

---

## 3. Setup instructions

**Prerequisites:** Python 3.11+ and a free Groq API key
(<https://console.groq.com>, no credit card).

```bash
# 1. Clone
git clone https://github.com/itsamanmanik/travel-planning-agent.git
cd travel-planning-agent

# 2. Configure the key
cp .env.example .env      # then set GROQ_API_KEY in .env

# 3. Install and run
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- Chat UI: <http://localhost:8000>
- Interactive API docs: <http://localhost:8000/docs>

Example API call:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Plan a 2-day trip to Paris, I love art\", \"user_id\": \"me\"}"
```

**Deployment (Render):** the repo includes a `Dockerfile`. On Render, create a
Web Service from the repo (auto-detects Docker), set the `GROQ_API_KEY`
environment variable, and choose the free instance type.

---

## 4. Evaluation results

`python evaluate.py` runs a scorecard. Latest run (`openai/gpt-oss-120b`):

| Check | Result |
| --- | --- |
| Tool reliability | 3/3 tools returned live data (≈1.6s / 6.2s / 2.8s) |
| Memory recall precision | 3/3 notes retrieved correctly by meaning |
| Planning accuracy | 4/4 correct tool choices (incl. clarifying when city missing) |
| End-to-end | 2-day itinerary in ≈11s using all three tools |
| **Total** | **10/10 checks passed** |

`pytest` runs four automated tests (no LLM key needed) — all pass.

**Cross-session memory (verified in production):** after stating "I'm vegetarian
and love forts" while planning Jaipur, a new session asking about Udaipur still
recalled both preferences and produced vegetarian, fort-focused suggestions.

---

## 5. Limitations

- **Rate limits:** free LLM tiers throttle heavy usage; fine for a demo.
- **Latency:** live web/Wikipedia calls add a few seconds — the cost of using
  real data instead of the model's memory.
- **Memory persistence on free hosting:** long-term memory lives on the
  container disk; on a free tier it can reset on redeploy. Fix: attach a
  persistent volume or point ChromaDB at a hosted store (one line in
  `app/config.py`).
- **Cold starts:** the free Render instance sleeps after ~15 minutes idle; the
  first request then takes ~50s to wake.
- **No authentication:** `user_id` is trusted as-is; a production version would
  add login.
