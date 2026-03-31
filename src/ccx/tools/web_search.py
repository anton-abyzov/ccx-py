"""Web search tool: search the web and return results."""

from __future__ import annotations

from typing import Any

import httpx

from ccx.tools.base import Tool, ToolContext, ToolResult

# Brave Search API (free tier, no key needed for basic)
SEARCH_URL = "https://html.duckduckgo.com/html/"
MAX_RESULTS = 10


class WebSearchTool(Tool):
    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Search the web and return results."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default 10).",
                },
            },
            "required": ["query"],
        }

    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        query = params["query"]
        max_results = params.get("max_results", MAX_RESULTS)

        try:
            async with httpx.AsyncClient(
                follow_redirects=True, timeout=15.0
            ) as client:
                response = await client.post(
                    SEARCH_URL,
                    data={"q": query},
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; ccx-py/0.1)",
                    },
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            return ToolResult(
                output=f"Search HTTP error {e.response.status_code}",
                is_error=True,
            )
        except httpx.RequestError as e:
            return ToolResult(output=f"Search request failed: {e}", is_error=True)

        results = _parse_results(response.text, max_results)
        if not results:
            return ToolResult(output=f"No results found for: {query}")

        output_lines = [f"Search results for: {query}\n"]
        for i, (title, url, snippet) in enumerate(results, 1):
            output_lines.append(f"{i}. {title}")
            output_lines.append(f"   {url}")
            if snippet:
                output_lines.append(f"   {snippet}")
            output_lines.append("")

        return ToolResult(
            output="\n".join(output_lines),
            metadata={"result_count": len(results), "query": query},
        )


def _parse_results(
    html: str, max_results: int
) -> list[tuple[str, str, str]]:
    """Extract search results from DuckDuckGo HTML response."""
    import re

    results: list[tuple[str, str, str]] = []

    # Find result links - DuckDuckGo wraps them in <a class="result__a">
    link_pattern = re.compile(
        r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
        re.DOTALL,
    )
    snippet_pattern = re.compile(
        r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
        re.DOTALL,
    )

    links = link_pattern.findall(html)
    snippets = snippet_pattern.findall(html)

    for i, (url, title) in enumerate(links[:max_results]):
        clean_title = re.sub(r"<[^>]+>", "", title).strip()
        snippet = ""
        if i < len(snippets):
            snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip()

        # DuckDuckGo wraps URLs in a redirect, extract the actual URL
        if "uddg=" in url:
            match = re.search(r"uddg=([^&]+)", url)
            if match:
                from urllib.parse import unquote
                url = unquote(match.group(1))

        if clean_title and url:
            results.append((clean_title, url, snippet))

    return results
