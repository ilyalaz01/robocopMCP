"""Manual copy-paste Gmail OAuth (no local server) — for WSL where the loopback
redirect cannot be reached.

Two steps (state persisted between them, incl. the PKCE code_verifier):

    uv run python scripts/gmail_oauth_manual.py url
        -> prints the consent URL; authorize in the browser.
           The redirect to http://localhost will fail to load — that is fine;
           copy the FULL address-bar URL (it contains ?code=...).

    uv run python scripts/gmail_oauth_manual.py exchange "<pasted code or URL>"
        -> exchanges the code for token.json, then sends the report and prints
           the Gmail message id.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from google_auth_oauthlib.flow import Flow

from robocop_mcp.reporting.gmail_auth import SCOPES, find_client_secret
from robocop_mcp.shared.config import ConfigManager

STATE_FILE = Path("/tmp/robocop_oauth_state.json")
REDIRECT = "http://localhost"  # registered loopback redirect of the desktop client


def _flow() -> Flow:
    # PKCE disabled: the desktop client_secret authenticates the exchange, and a
    # two-process copy-paste flow cannot reliably round-trip the code_verifier.
    creds = find_client_secret(ConfigManager().root)
    return Flow.from_client_secrets_file(str(creds), scopes=SCOPES, redirect_uri=REDIRECT,
                                         autogenerate_code_verifier=False)


def cmd_url() -> None:
    flow = _flow()
    auth_url, state = flow.authorization_url(access_type="offline", prompt="consent")
    STATE_FILE.write_text(json.dumps({"state": state}))
    print(auth_url)


def _extract_code(pasted: str) -> str:
    """Accept either a bare code or the full redirected URL; return the raw code."""
    if pasted.startswith("http"):
        qs = parse_qs(urlparse(pasted).query)
        return qs.get("code", [""])[0]
    return unquote(pasted.strip())


def cmd_exchange(pasted: str) -> None:
    flow = _flow()
    flow.fetch_token(code=_extract_code(pasted))  # no PKCE verifier (see _flow)
    creds = flow.credentials
    token_path = ConfigManager().root / "token.json"
    token_path.write_text(creds.to_json())
    print("token.json created")
    _send_report(creds)


def _send_report(creds) -> None:
    from googleapiclient.discovery import build

    from robocop_mcp.sdk.sdk import MarlSDK
    sdk = MarlSDK()
    series = sdk.run_series(match_id="email_send")
    report = sdk.build_internal_report(series)
    service = build("gmail", "v1", credentials=creds)
    recipient = sdk.cfg.get("report", "recipient_email", default="")
    result = sdk.send_report(series, report=report, dry_run=False,
                             service_factory=lambda: service)
    print("SEND RESULT:", json.dumps(result))
    if result.get("sent") and result.get("message_id"):
        print(f"CONFIRMED: email SENT to {recipient} (message id {result['message_id']}).")


def main() -> None:
    if len(sys.argv) >= 2 and sys.argv[1] == "url":
        cmd_url()
    elif len(sys.argv) >= 3 and sys.argv[1] == "exchange":
        cmd_exchange(sys.argv[2])
    else:
        print("usage: gmail_oauth_manual.py url | exchange '<code or redirect URL>'")


if __name__ == "__main__":
    main()
