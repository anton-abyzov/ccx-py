"""Tests for the permission system."""

import pytest

from ccx.permissions.classifier import PermissionClassifier, RiskLevel
from ccx.permissions.modes import PermissionMode
from ccx.permissions.rules import PermissionRule, PermissionRuleSet, RuleAction


class TestPermissionClassifier:
    def setup_method(self):
        self.classifier = PermissionClassifier()

    def test_safe_tools(self):
        assert self.classifier.classify("file_read", {}) == RiskLevel.SAFE
        assert self.classifier.classify("glob", {}) == RiskLevel.SAFE
        assert self.classifier.classify("grep", {}) == RiskLevel.SAFE

    def test_low_risk_tools(self):
        assert self.classifier.classify("file_write", {}) == RiskLevel.LOW
        assert self.classifier.classify("file_edit", {}) == RiskLevel.LOW

    def test_medium_risk_tools(self):
        assert self.classifier.classify("bash", {"command": "ls"}) == RiskLevel.MEDIUM
        assert self.classifier.classify("web_fetch", {}) == RiskLevel.MEDIUM

    def test_dangerous_bash_elevated(self):
        assert self.classifier.classify("bash", {"command": "rm -rf /"}) == RiskLevel.HIGH
        assert self.classifier.classify("bash", {"command": "sudo apt install"}) == RiskLevel.HIGH
        assert self.classifier.classify("bash", {"command": "git push --force"}) == RiskLevel.HIGH

    def test_unknown_tool_medium(self):
        assert self.classifier.classify("custom_tool", {}) == RiskLevel.MEDIUM

    def test_needs_permission_bypass(self):
        assert not self.classifier.needs_permission("bash", {}, PermissionMode.BYPASS)

    def test_needs_permission_plan(self):
        assert self.classifier.needs_permission("file_read", {}, PermissionMode.PLAN)

    def test_needs_permission_accept_edits(self):
        assert not self.classifier.needs_permission(
            "file_write", {}, PermissionMode.ACCEPT_EDITS
        )
        assert self.classifier.needs_permission(
            "bash", {"command": "ls"}, PermissionMode.ACCEPT_EDITS
        )

    def test_needs_permission_default(self):
        assert not self.classifier.needs_permission("file_read", {}, PermissionMode.DEFAULT)
        assert self.classifier.needs_permission("file_write", {}, PermissionMode.DEFAULT)


class TestPermissionRules:
    def test_rule_matches_tool(self):
        rule = PermissionRule(tool="bash", action=RuleAction.ALLOW)
        assert rule.matches_tool("bash")
        assert not rule.matches_tool("file_read")

    def test_rule_glob_pattern(self):
        rule = PermissionRule(tool="file_*", action=RuleAction.ALLOW)
        assert rule.matches_tool("file_read")
        assert rule.matches_tool("file_write")
        assert not rule.matches_tool("bash")

    def test_rule_path_patterns(self):
        rule = PermissionRule(
            tool="file_write",
            action=RuleAction.ALLOW,
            path_patterns=["/home/user/project/*"],
        )
        assert rule.matches_path("/home/user/project/src/file.py")
        assert not rule.matches_path("/etc/passwd")

    def test_rule_evaluate(self):
        rule = PermissionRule(tool="bash", action=RuleAction.ALLOW)
        assert rule.evaluate("bash", {}) == RuleAction.ALLOW
        assert rule.evaluate("other", {}) is None

    def test_ruleset_first_match(self):
        rules = PermissionRuleSet()
        rules.add(PermissionRule(tool="bash", action=RuleAction.DENY))
        rules.add(PermissionRule(tool="*", action=RuleAction.ALLOW))

        assert rules.evaluate("bash", {}) == RuleAction.DENY
        assert rules.evaluate("file_read", {}) == RuleAction.ALLOW

    def test_ruleset_default_ask(self):
        rules = PermissionRuleSet()
        assert rules.evaluate("anything", {}) == RuleAction.ASK
