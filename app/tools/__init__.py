"""Tool registry.

Each tool is a plain function, described in TOOL_CATALOG so the planner can
select tools by name. run_tool() dispatches a call and never raises.
"""

from .weather import get_weather
from .websearch import web_search
from .wiki import wiki_research

# Descriptions the planner reads to choose tools for a request.
TOOL_CATALOG = [
    {
        "name": "get_weather",
        "description": "Get the multi-day weather forecast for a city. "
                       "Use this to plan indoor vs outdoor activities.",
        "args": {"city": "Name of the city, e.g. 'Tokyo'"},
    },
    {
        "name": "web_search",
        "description": "Search the live web for up-to-date info: opening hours, "
                       "events, tickets, restaurants, local tips.",
        "args": {"query": "What to search for, e.g. 'best ramen in Shibuya'"},
    },
    {
        "name": "wiki_research",
        "description": "Deep research on a city's top attractions using Wikipedia "
                       "(multi-hop). Use this for reliable background on what to see.",
        "args": {
            "city": "Name of the city, e.g. 'Paris'",
            "interests": "Optional comma-separated interests, e.g. 'museums, food'",
        },
    },
]

_TOOL_FUNCTIONS = {
    "get_weather": get_weather,
    "web_search": web_search,
    "wiki_research": wiki_research,
}


def run_tool(name: str, args: dict) -> dict:
    """Run one tool by name. Failures are returned as an 'error' field so a
    single failing tool never breaks the request."""
    func = _TOOL_FUNCTIONS.get(name)
    if func is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return func(**(args or {}))
    except Exception as e:
        return {"error": f"Tool '{name}' failed: {e}"}
