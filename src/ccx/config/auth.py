"""OAuth token resolution from Claude Code credentials."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def resolve_auth() -> tuple[str, bool, str]:
    """Resolve authentication credentials in priority order.

    Returns:
        Tuple of (key_or_token, is_oauth, display_name).

    Raises:
        RuntimeError: If no authentication source is found.
    """
    # 1. Environment variable
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key, False, "API Key"

    # 2. macOS Keychain
    if sys.platform == "darwin":
        token, sub = _read_keychain()
        if token:
            return token, True, f"Claude {sub}"

    # 3. Credentials file fallback
    token, sub = _read_credentials_file()
    if token:
        return token, True, f"Claude {sub}"

    raise RuntimeError(
        "No authentication found.\n\n"
        "Set ANTHROPIC_API_KEY or log in with: claude auth"
    )


def _read_keychain() -> tuple[str, str]:
    """Read OAuth token from macOS Keychain."""
    try:
        user = os.environ.get("USER", "")
        if not user:
            return "", ""
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-a", user,
                "-w",
                "-s", "Claude Code-credentials",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return _parse_oauth_json(result.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "", ""


def _read_credentials_file() -> tuple[str, str]:
    """Read OAuth token from ~/.claude/.credentials.json."""
    creds_path = Path.home() / ".claude" / ".credentials.json"
    try:
        if creds_path.exists():
            return _parse_oauth_json(creds_path.read_text())
    except (OSError, PermissionError):
        pass
    return "", ""


def _parse_oauth_json(raw: str) -> tuple[str, str]:
    """Extract access token and subscription type from credentials JSON."""
    try:
        data = json.loads(raw)
        token = data.get("claudeAiOauth", {}).get("accessToken", "")
        if not token:
            return "", ""
        sub_type = data.get("claudeAiSubscriptionType", "Pro")
        return token, sub_type.title()
    except (json.JSONDecodeError, AttributeError):
        return "", ""
