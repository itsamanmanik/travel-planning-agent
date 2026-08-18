---
title: Travel Planning AI Agent
emoji: 🧭
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 8000
pinned: false
---

# Travel Planning AI Agent

An AI agent that plans a personalized 2-day trip to any city. It decides which
tools to call on its own, remembers a user's preferences between sessions, and
grounds its suggestions in real data (weather, Wikipedia, live web). It runs
entirely on free services — no paid APIs.

Example: *"Plan a 2-day trip to Tokyo. I'm vegetarian and love museums."*
→ it checks the forecast, researches attractions, searches the web, notes that
the user is vegetarian, and writes a day-by-day itinerary.

## How the requirements map to the code

| Requirement | Where it lives |
| --- | --- |
| 3+ tools, chosen dynamically | `app/tools/` — weather, web search, Wikipedia; the planner picks which to use |
| Short-term memory | `ShortTermMemory` in `app/memory.py` (conversation, in RAM) |
| Long-term memory (vector DB) | `LongTermMemory` in `app/memory.py` (ChromaDB, semantic recall) |
| Planning / reasoning | `app/planner.py` breaks the goal into tool calls |
| Multi-hop RAG | `app/tools/wiki.py` retrieves in two hops (city → attractions → details) |
| Conversational API + UI | `app/main.py` (FastAPI `/chat`) + `static/index.html` |
| Constraints / multilingual (bonus) | preferences (vegetarian, budget, pets) respected; replies follow the user's language |

## Stack (everything free)

| Part | Choice | Notes |
| --- | --- | --- |
| LLM | Groq — GPT OSS 120B | free key, no card |
| Vector DB | ChromaDB | local, on disk, bundled embeddings |
| Web search | DuckDuckGo (`ddgs`) | no key |
| Weather | Open-Meteo | no key |
| Attractions | Wikipedia API | no key |
| API / server | FastAPI + Uvicorn | — |

## Running it locally

1. Get a free Groq key at <https://console.groq.com>, then copy `.env.example`
   to `.env` and set `GROQ_API_KEY`.
2. Start it:

   ```bash
   # Windows PowerShell
   ./run.ps1
   # Git Bash / macOS / Linux
   ./run.sh
   # or manually, in an activated venv:
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

3. Open <http://localhost:8000> for the chat UI, or <http://localhost:8000/docs>
   for the API docs. To call the API directly:

   ```bash
   curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d "{\"message\": \"Plan a 2-day trip to Paris, I love art\", \"user_id\": \"me\"}"
   ```

## Results

`python evaluate.py` runs a scorecard. Latest run (`openai/gpt-oss-120b`):

- Tool reliability: 3/3 tools returned live data
- Memory recall: 3/3 notes retrieved correctly by meaning
- Planning accuracy: 4/4 correct tool choices (including asking when the city is missing)
- End-to-end: a 2-day itinerary in ~11s using all three tools
- Total: 10/10

`python demo.py` shows cross-session memory: after saying "I'm vegetarian and
love temples" for a Kyoto trip, a new session asking about Osaka still
recommends a historic temple and a vegan restaurant — the preference is pulled
from the ChromaDB store without repeating it.

`pytest` runs the fast automated tests (no LLM key needed).

## Project layout

```
travel-agent/
├── app/
│   ├── main.py         FastAPI: REST API + serves the UI
│   ├── agent.py        request flow: recall → plan → act → answer → learn
│   ├── planner.py      picks which tools to run
│   ├── llm.py          Groq wrapper
│   ├── memory.py       short-term + long-term (vector DB) memory
│   ├── config.py       settings from .env
│   └── tools/          get_weather, web_search, wiki_research (multi-hop RAG)
├── static/index.html   chat UI
├── evaluate.py         scorecard
├── demo.py             scripted showcase
├── tests/              pytest smoke tests
├── Dockerfile          for free deployment
└── ARCHITECTURE.md     design notes
```

## Deploying (free)

The `Dockerfile` runs anywhere.

- **Hugging Face Spaces:** new Docker Space → upload the files → add
  `GROQ_API_KEY` as a Secret.
- **Render:** new Web Service → connect the repo → it detects the Dockerfile →
  add `GROQ_API_KEY`. The free tier sleeps when idle and wakes on the next request.

See `ARCHITECTURE.md` for the design reasoning and trade-offs.
