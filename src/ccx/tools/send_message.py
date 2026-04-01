"""Send message tool: send a message to a teammate or broadcast."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ccx.tools.base import Tool, ToolContext, ToolResult

TEAMS_ROOT = Path.home() / ".claude" / "teams"


class SendMessageTool(Tool):
    @property
    def name(self) -> str:
        return "send_message"

    @property
    def description(self) -> str:
        return "Send a message to a teammate or broadcast to all team members."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient name or 'all' for broadcast.",
                },
                "message": {
                    "type": "string",
                    "description": "Message content.",
                },
                "summary": {
                    "type": "string",
                    "description": "Optional short summary of the message.",
                },
            },
            "required": ["to", "message"],
        }

    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        to = params["to"]
        message = params["message"]
        summary = params.get("summary", "")

        # Find first team directory
        if not TEAMS_ROOT.exists():
            return ToolResult(output="No teams found.", is_error=True)

        team_dirs = [d for d in TEAMS_ROOT.iterdir() if d.is_dir()]
        if not team_dirs:
            return ToolResult(output="No teams found.", is_error=True)

        team_dir = team_dirs[0]
        messages_dir = team_dir / "messages"

        try:
            messages_dir.mkdir(parents=True, exist_ok=True)

            entry = {
                "from": "agent",
                "to": to,
                "message": message,
                "summary": summary,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            msg_file = messages_dir / f"{to}.jsonl"
            with msg_file.open("a") as f:
                f.write(json.dumps(entry) + "\n")
        except OSError as e:
            return ToolResult(output=f"Failed to send message: {e}", is_error=True)

        return ToolResult(
            output=f"Message sent to '{to}' in team '{team_dir.name}'.",
            metadata={"team": team_dir.name, "to": to},
        )
