"""Permission modes that control tool execution authorization."""

from __future__ import annotations

from enum import Enum


class PermissionMode(str, Enum):
    """How the system handles tool authorization."""

    DEFAULT = "default"          # Prompt user for risky tools
    ACCEPT_EDITS = "acceptEdits"  # Auto-approve file edits
    BYPASS = "bypass"            # Auto-approve everything
    PLAN = "plan"                # Read-only, no execution
