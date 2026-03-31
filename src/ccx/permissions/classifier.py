"""Classify tool calls by risk level."""

from __future__ import annotations

from enum import IntEnum
from typing import Any

from ccx.permissions.modes import PermissionMode


class RiskLevel(IntEnum):
    SAFE = 0       # Read-only operations
    LOW = 1        # File edits in project
    MEDIUM = 2     # Shell commands, network access
    HIGH = 3       # Destructive operations


# Tool name -> base risk level
_TOOL_RISK: dict[str, RiskLevel] = {
    "file_read": RiskLevel.SAFE,
    "glob": RiskLevel.SAFE,
    "grep": RiskLevel.SAFE,
    "file_write": RiskLevel.LOW,
    "file_edit": RiskLevel.LOW,
    "bash": RiskLevel.MEDIUM,
    "web_fetch": RiskLevel.MEDIUM,
}

# Command patterns that elevate risk
_DANGEROUS_PATTERNS = [
    "rm -rf",
    "rm -r",
    "git push --force",
    "git reset --hard",
    "drop table",
    "drop database",
    "sudo",
    "chmod 777",
    "> /dev/",
    "mkfs",
    "dd if=",
]


class PermissionClassifier:
    """Classifies tool calls to determine if user permission is needed."""

    def classify(self, tool_name: str, params: dict[str, Any]) -> RiskLevel:
        """Determine the risk level of a tool call."""
        base_risk = _TOOL_RISK.get(tool_name, RiskLevel.MEDIUM)

        # Elevate bash commands with dangerous patterns
        if tool_name == "bash":
            command = params.get("command", "")
            for pattern in _DANGEROUS_PATTERNS:
                if pattern in command.lower():
                    return RiskLevel.HIGH

        return base_risk

    def needs_permission(
        self,
        tool_name: str,
        params: dict[str, Any],
        mode: PermissionMode,
    ) -> bool:
        """Check if a tool call needs explicit user permission."""
        match mode:
            case PermissionMode.BYPASS:
                return False
            case PermissionMode.PLAN:
                return True  # Everything needs permission in plan mode
            case PermissionMode.ACCEPT_EDITS:
                risk = self.classify(tool_name, params)
                return risk >= RiskLevel.MEDIUM
            case PermissionMode.DEFAULT:
                risk = self.classify(tool_name, params)
                return risk >= RiskLevel.LOW
