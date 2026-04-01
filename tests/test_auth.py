"""Tests for OAuth auth resolution."""

import json
from unittest.mock import patch

import pytest

from ccx.config.auth import _parse_oauth_json, resolve_auth


class TestParseOAuthJSON:
    def test_valid_max(self):
        raw = json.dumps({
            "claudeAiOauth": {"accessToken": "tok_abc123"},
            "claudeAiSubscriptionType": "max",
            "email": "user@example.com",
        })
        token, sub, email = _parse_oauth_json(raw)
        assert token == "tok_abc123"
        assert sub == "Max"
        assert email == "user@example.com"

    def test_pro_default(self):
        raw = json.dumps({"claudeAiOauth": {"accessToken": "tok_xyz"}})
        token, sub, email = _parse_oauth_json(raw)
        assert token == "tok_xyz"
        assert sub == "Pro"
        assert email == ""

    def test_no_token(self):
        raw = json.dumps({"claudeAiOauth": {}})
        token, sub, email = _parse_oauth_json(raw)
        assert token == ""
        assert sub == ""
        assert email == ""

    def test_invalid_json(self):
        token, sub, email = _parse_oauth_json("not json")
        assert token == ""
        assert sub == ""
        assert email == ""

    def test_empty_string(self):
        token, sub, email = _parse_oauth_json("")
        assert token == ""
        assert sub == ""
        assert email == ""


class TestResolveAuth:
    def test_env_var(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test123")
        key, is_oauth, display = resolve_auth()
        assert key == "sk-ant-test123"
        assert is_oauth is False
        assert display == "API Key"

    def test_no_auth_raises(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with patch("ccx.config.auth._read_keychain", return_value=("", "", "")):
            with patch("ccx.config.auth._read_credentials_file", return_value=("", "", "")):
                with pytest.raises(RuntimeError, match="No authentication found"):
                    resolve_auth()

    def test_keychain_fallback(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with patch("ccx.config.auth.sys") as mock_sys:
            mock_sys.platform = "darwin"
            with patch("ccx.config.auth._read_keychain", return_value=("tok_key", "Max", "")):
                key, is_oauth, display = resolve_auth()
                assert key == "tok_key"
                assert is_oauth is True
                assert display == "Claude Max"

    def test_keychain_with_email(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with patch("ccx.config.auth.sys") as mock_sys:
            mock_sys.platform = "darwin"
            with patch("ccx.config.auth._read_keychain", return_value=("tok_key", "Max", "user@example.com")):
                key, is_oauth, display = resolve_auth()
                assert key == "tok_key"
                assert is_oauth is True
                assert display == "Claude Max (user@example.com)"

    def test_file_fallback(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with patch("ccx.config.auth._read_keychain", return_value=("", "", "")):
            with patch("ccx.config.auth._read_credentials_file", return_value=("tok_file", "Pro", "")):
                key, is_oauth, display = resolve_auth()
                assert key == "tok_file"
                assert is_oauth is True
                assert display == "Claude Pro"
