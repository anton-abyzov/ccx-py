"""Server-Sent Events (SSE) parser for Claude streaming API."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from ccx.api.types import StreamEvent, StreamEventType


@dataclass
class SSEEvent:
    """Raw SSE event before parsing into StreamEvent."""

    event: str = ""
    data: str = ""
    id: str = ""
    retry: int | None = None
    _data_lines: list[str] = field(default_factory=list)

    def append_data(self, line: str) -> None:
        self._data_lines.append(line)

    def finalize(self) -> None:
        self.data = "\n".join(self._data_lines)


async def parse_sse(lines: AsyncIterator[str]) -> AsyncIterator[StreamEvent]:
    """Parse an async stream of SSE lines into StreamEvent objects.

    Follows the SSE specification: events are separated by blank lines,
    each line is either a field:value pair or a comment (starting with :).
    """
    current = SSEEvent()

    async for raw_line in lines:
        line = raw_line.rstrip("\n").rstrip("\r")

        if not line:
            # Blank line = dispatch event
            if current.event or current._data_lines:
                current.finalize()
                event = _parse_event(current)
                if event is not None:
                    yield event
            current = SSEEvent()
            continue

        if line.startswith(":"):
            # Comment line, ignore
            continue

        if ":" in line:
            field_name, _, value = line.partition(":")
            if value.startswith(" "):
                value = value[1:]
        else:
            field_name = line
            value = ""

        match field_name:
            case "event":
                current.event = value
            case "data":
                current.append_data(value)
            case "id":
                current.id = value
            case "retry":
                try:
                    current.retry = int(value)
                except ValueError:
                    pass

    # Handle trailing event without final newline
    if current.event or current._data_lines:
        current.finalize()
        event = _parse_event(current)
        if event is not None:
            yield event


def _parse_event(sse: SSEEvent) -> StreamEvent | None:
    """Convert a raw SSE event into a typed StreamEvent."""
    if not sse.data:
        return None

    try:
        data = json.loads(sse.data)
    except json.JSONDecodeError:
        return None

    event_type_str = sse.event or data.get("type", "")

    try:
        event_type = StreamEventType(event_type_str)
    except ValueError:
        return None

    return StreamEvent(
        type=event_type,
        index=data.get("index"),
        message=data.get("message"),
        content_block=data.get("content_block"),
        delta=data.get("delta"),
        usage=data.get("usage"),
        error=data.get("error"),
    )
