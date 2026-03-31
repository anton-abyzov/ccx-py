"""Permission rules: allow/deny patterns for tool calls."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RuleAction(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


@dataclass
class PermissionRule:
    """A single permission rule matching tool calls."""

    tool: str                              # Tool name or glob pattern
    action: RuleAction = RuleAction.ASK
    path_patterns: list[str] = field(default_factory=list)  # Allowed path globs

    def matches_tool(self, tool_name: str) -> bool:
        return fnmatch.fnmatch(tool_name, self.tool)

    def matches_path(self, path: str) -> bool:
        if not self.path_patterns:
            return True
        return any(fnmatch.fnmatch(path, p) for p in self.path_patterns)

    def evaluate(self, tool_name: str, params: dict[str, Any]) -> RuleAction | None:
        if not self.matches_tool(tool_name):
            return None

        # Check path-based rules
        for key in ("file_path", "path", "command"):
            if key in params and self.path_patterns:
                if not self.matches_path(str(params[key])):
                    return RuleAction.DENY

        return self.action


@dataclass
class PermissionRuleSet:
    """Ordered set of permission rules, first match wins."""

    rules: list[PermissionRule] = field(default_factory=list)

    def add(self, rule: PermissionRule) -> None:
        self.rules.append(rule)

    def evaluate(self, tool_name: str, params: dict[str, Any]) -> RuleAction:
        for rule in self.rules:
            result = rule.evaluate(tool_name, params)
            if result is not None:
                return result
        return RuleAction.ASK  # Default to asking
