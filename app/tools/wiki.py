"""Multi-hop retrieval over Wikipedia for attraction research.

Retrieval runs in two dependent hops: first resolve a city to its top
attraction page titles, then fetch a summary for each of those pages. The
aggregated text grounds the final itinerary in real sources.
"""

import requests

SEARCH_URL = "https://en.wikipedia.org/w/api.php"
SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
HEADERS = {"User-Agent": "TravelPlannerAgent/1.0"}


def _search_titles(query: str, limit: int = 4) -> list[str]:
    """Return the top Wikipedia page titles matching a search query."""
    params = {
        "action": "query", "list": "search", "srsearch": query,
        "srlimit": limit, "format": "json",
    }
    data = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=15).json()
    return [item["title"] for item in data.get("query", {}).get("search", [])]


def _get_summary(title: str) -> dict | None:
    """Return a short summary for a single Wikipedia page title."""
    resp = requests.get(SUMMARY_URL + title.replace(" ", "_"),
                        headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        return None
    data = resp.json()
    extract = data.get("extract")
    if not extract:
        return None
    return {"title": data.get("title", title), "summary": extract}


def wiki_research(city: str, interests: str = "") -> dict:
    """Return a city overview plus summaries of its top attractions."""

    # Hop 1: resolve the city (and any interests) to candidate attraction titles.
    if interests:
        hop1_query = f"{interests} attractions in {city}"
    else:
        hop1_query = f"tourist attractions in {city}"

    attraction_titles = _search_titles(hop1_query, limit=5)
    city_summary = _get_summary(city)

    # Hop 2: fetch a summary for each candidate attraction.
    attractions = []
    for title in attraction_titles:
        summary = _get_summary(title)
        if summary:
            attractions.append(summary)
        if len(attractions) >= 4:
            break

    if not attractions and not city_summary:
        return {"error": f"Could not find Wikipedia info for '{city}'."}

    return {
        "city": city,
        "city_overview": city_summary["summary"] if city_summary else "",
        "attractions": attractions,
        "hops": 2,
        "source": "Wikipedia",
    }
