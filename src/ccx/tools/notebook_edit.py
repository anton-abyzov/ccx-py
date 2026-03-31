"""Notebook edit tool: edit Jupyter .ipynb notebook cells."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ccx.tools.base import Tool, ToolContext, ToolResult


class NotebookEditTool(Tool):
    @property
    def name(self) -> str:
        return "notebook_edit"

    @property
    def description(self) -> str:
        return "Edit cells in a Jupyter notebook (.ipynb file)."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the .ipynb file.",
                },
                "cell_index": {
                    "type": "integer",
                    "description": "Index of the cell to edit (0-based).",
                },
                "new_source": {
                    "type": "string",
                    "description": "New source content for the cell.",
                },
                "cell_type": {
                    "type": "string",
                    "enum": ["code", "markdown", "raw"],
                    "description": "Cell type (only for insert operations).",
                },
                "operation": {
                    "type": "string",
                    "enum": ["replace", "insert", "delete"],
                    "description": "Operation: replace (default), insert, or delete.",
                },
            },
            "required": ["path"],
        }

    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        path_str = params["path"]
        path = Path(path_str)
        if not path.is_absolute():
            path = ctx.working_dir / path

        operation = params.get("operation", "replace")

        if not path.exists():
            if operation == "insert" and params.get("new_source") is not None:
                # Create new notebook
                notebook = _new_notebook()
            else:
                return ToolResult(
                    output=f"Notebook not found: {path}", is_error=True
                )
        else:
            try:
                notebook = json.loads(path.read_text("utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                return ToolResult(
                    output=f"Failed to read notebook: {e}", is_error=True
                )

        cells = notebook.get("cells", [])

        if operation == "replace":
            return self._replace(cells, params, notebook, path)
        elif operation == "insert":
            return self._insert(cells, params, notebook, path)
        elif operation == "delete":
            return self._delete(cells, params, notebook, path)
        else:
            return ToolResult(
                output=f"Unknown operation: {operation}", is_error=True
            )

    def _replace(
        self,
        cells: list[dict[str, Any]],
        params: dict[str, Any],
        notebook: dict[str, Any],
        path: Path,
    ) -> ToolResult:
        cell_index = params.get("cell_index")
        new_source = params.get("new_source")

        if cell_index is None or new_source is None:
            return ToolResult(
                output="replace requires cell_index and new_source",
                is_error=True,
            )

        if cell_index < 0 or cell_index >= len(cells):
            return ToolResult(
                output=f"Cell index {cell_index} out of range (0-{len(cells) - 1})",
                is_error=True,
            )

        cells[cell_index]["source"] = _to_source_lines(new_source)
        if params.get("cell_type"):
            cells[cell_index]["cell_type"] = params["cell_type"]
        # Clear outputs on code cells
        if cells[cell_index].get("cell_type") == "code":
            cells[cell_index]["outputs"] = []
            cells[cell_index]["execution_count"] = None

        return _save(notebook, path, f"Replaced cell {cell_index}")

    def _insert(
        self,
        cells: list[dict[str, Any]],
        params: dict[str, Any],
        notebook: dict[str, Any],
        path: Path,
    ) -> ToolResult:
        new_source = params.get("new_source", "")
        cell_type = params.get("cell_type", "code")
        cell_index = params.get("cell_index", len(cells))

        new_cell: dict[str, Any] = {
            "cell_type": cell_type,
            "source": _to_source_lines(new_source),
            "metadata": {},
        }
        if cell_type == "code":
            new_cell["outputs"] = []
            new_cell["execution_count"] = None

        idx = max(0, min(cell_index, len(cells)))
        cells.insert(idx, new_cell)
        notebook["cells"] = cells

        return _save(notebook, path, f"Inserted {cell_type} cell at index {idx}")

    def _delete(
        self,
        cells: list[dict[str, Any]],
        params: dict[str, Any],
        notebook: dict[str, Any],
        path: Path,
    ) -> ToolResult:
        cell_index = params.get("cell_index")
        if cell_index is None:
            return ToolResult(
                output="delete requires cell_index", is_error=True
            )
        if cell_index < 0 or cell_index >= len(cells):
            return ToolResult(
                output=f"Cell index {cell_index} out of range (0-{len(cells) - 1})",
                is_error=True,
            )

        removed = cells.pop(cell_index)
        notebook["cells"] = cells
        return _save(
            notebook,
            path,
            f"Deleted cell {cell_index} ({removed.get('cell_type', 'unknown')})",
        )


def _to_source_lines(source: str) -> list[str]:
    """Convert source string to notebook source format (list of lines)."""
    lines = source.split("\n")
    result = []
    for i, line in enumerate(lines):
        if i < len(lines) - 1:
            result.append(line + "\n")
        elif line:  # Don't add empty trailing line
            result.append(line)
    return result


def _save(notebook: dict[str, Any], path: Path, message: str) -> ToolResult:
    """Save notebook to disk."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")
    except OSError as e:
        return ToolResult(output=f"Failed to save notebook: {e}", is_error=True)
    return ToolResult(output=message, metadata={"path": str(path)})


def _new_notebook() -> dict[str, Any]:
    """Create a minimal empty notebook structure."""
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11.0"},
        },
        "cells": [],
    }
