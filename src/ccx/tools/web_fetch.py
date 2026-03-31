"""Web fetch tool: HTTP GET with content extraction."""

from __future__ import annotations

from typing import Any

import httpx

from ccx.tools.base import Tool, ToolContext, ToolResult

MAX_CONTENT_BYTES = 256_000


class WebFetchTool(Tool):
    @property
    def name(self) -> str:
        return "web_fetch"

    @property
    def description(self) -> str:
        return "Fetch a URL and return its text content."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to fetch.",
                },
            },
            "required": ["url"],
        }

    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        url = params["url"]

        try:
            async with httpx.AsyncClient(
                follow_redirects=True, timeout=30.0
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            return ToolResult(output=f"HTTP {e.response.status_code}: {url}", is_error=True)
        except httpx.RequestError as e:
            return ToolResult(output=f"Request failed: {e}", is_error=True)

        content = response.text
        if len(content) > MAX_CONTENT_BYTES:
            content = content[:MAX_CONTENT_BYTES] + "\n... (truncated)"

        return ToolResult(
            output=content,
            metadata={"status_code": response.status_code, "url": str(response.url)},
        )
