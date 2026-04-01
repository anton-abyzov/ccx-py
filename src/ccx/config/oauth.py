"""OAuth PKCE login flow for Claude AI."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import subprocess
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Event
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
AUTHORIZE_URL = "https://claude.ai/oauth/authorize"
TOKEN_URL = "https://platform.claude.com/v1/oauth/token"
SCOPES = "user:profile user:inference"
KEYCHAIN_SERVICE = "Claude Code-credentials"


def _generate_pkce() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge."""
    verifier_bytes = secrets.token_bytes(32)
    code_verifier = base64.urlsafe_b64encode(verifier_bytes).rstrip(b"=").decode("ascii")
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge


def _save_to_keychain(creds_json: str) -> None:
    """Save credentials to macOS Keychain."""
    if sys.platform != "darwin":
        return
    user = os.environ.get("USER", "")
    if not user:
        return
    # Delete existing entry (ignore errors if it doesn't exist)
    subprocess.run(
        ["security", "delete-generic-password", "-a", user, "-s", KEYCHAIN_SERVICE],
        capture_output=True,
        timeout=5,
    )
    subprocess.run(
        [
            "security",
            "add-generic-password",
            "-a", user,
            "-s", KEYCHAIN_SERVICE,
            "-w", creds_json,
        ],
        capture_output=True,
        text=True,
        timeout=5,
    )


def _save_to_credentials_file(creds_json: str) -> None:
    """Save credentials to ~/.claude/.credentials.json."""
    claude_dir = Path.home() / ".claude"
    claude_dir.mkdir(exist_ok=True)
    creds_path = claude_dir / ".credentials.json"
    creds_path.write_text(creds_json)


def run_oauth_login() -> None:
    """Execute the full OAuth PKCE login flow."""
    code_verifier, code_challenge = _generate_pkce()

    auth_code_holder: dict[str, str] = {}
    server_ready = Event()
    callback_received = Event()

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/oauth/callback":
                params = parse_qs(parsed.query)
                code = params.get("code", [""])[0]
                if code:
                    auth_code_holder["code"] = code
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(
                        b"<html><body><h2>Login successful!</h2>"
                        b"<p>You can close this tab.</p></body></html>"
                    )
                else:
                    error = params.get("error", ["unknown"])[0]
                    self.send_response(400)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(f"<html><body><h2>Error: {error}</h2></body></html>".encode())
                callback_received.set()
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            pass  # Suppress HTTP server logs

    server = HTTPServer(("127.0.0.1", 0), CallbackHandler)
    port = server.server_address[1]
    redirect_uri = f"http://localhost:{port}/oauth/callback"

    auth_params = urlencode({
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": SCOPES,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    })
    auth_url = f"{AUTHORIZE_URL}?{auth_params}"

    print(f"Opening browser for authentication...")
    webbrowser.open(auth_url)
    print("Waiting for authorization callback...")

    # Handle a single request (the callback)
    server.handle_request()

    if "code" not in auth_code_holder:
        print("Error: No authorization code received.", file=sys.stderr)
        sys.exit(1)

    auth_code = auth_code_holder["code"]

    # Exchange code for token
    token_data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "code": auth_code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }

    resp = httpx.post(
        TOKEN_URL,
        data=token_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )

    if resp.status_code != 200:
        print(f"Token exchange failed ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)

    token_response = resp.json()
    access_token = token_response.get("access_token", "")
    if not access_token:
        print("Error: No access token in response.", file=sys.stderr)
        sys.exit(1)

    # Build credentials JSON matching Claude Code format
    creds = {
        "claudeAiOauth": {
            "accessToken": access_token,
        },
    }
    if "refresh_token" in token_response:
        creds["claudeAiOauth"]["refreshToken"] = token_response["refresh_token"]
    if "expires_in" in token_response:
        creds["claudeAiOauth"]["expiresIn"] = token_response["expires_in"]

    creds_json = json.dumps(creds)

    _save_to_keychain(creds_json)
    _save_to_credentials_file(creds_json)

    print("Login successful!")

    server.server_close()
