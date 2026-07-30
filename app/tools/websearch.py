"""Live web search tool backed by DuckDuckGo (no API key required)."""

from ddgs import DDGS


def web_search(query: str, max_results: int = 5) -> dict:
    """Return the top web results for a query as title/snippet/url."""
    results = []
    with DDGS() as ddgs:
        for hit in ddgs.text(query, max_results=max_results):
            results.append({
                "title": hit.get("title", ""),
                "snippet": hit.get("body", ""),
                "url": hit.get("href", ""),
            })

    if not results:
        return {"error": f"No web results for '{query}'."}

    return {"query": query, "results": results}
