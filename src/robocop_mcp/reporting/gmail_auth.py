"""Gmail OAuth — mint/refresh token.json and build the live Gmail service.

This is the interactive, network-touching boundary (the Phase-11 "DO WITH ILYA"
step), so it is excluded from coverage. It uses the installed-app loopback flow:
the user consents once in a browser, and the refresh token is cached in
``token.json``. Both the client-secret file and ``token.json`` are git-ignored —
never commit them (the repo is public). Least-privilege scope: gmail.send only.
"""

from __future__ import annotations

from pathlib import Path

# Sending is all we need; we never read the mailbox (principle of least privilege).
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def find_client_secret(root: Path) -> Path:  # pragma: no cover - filesystem lookup
    """Locate the OAuth client file in ``root`` (credentials.json or client_secret_*)."""
    candidates = [root / "credentials.json", *sorted(root.glob("client_secret_*.json"))]
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError(
        f"No OAuth client file in {root} (expected credentials.json or client_secret_*.json)")


def build_gmail_service(creds_path: Path, token_path: Path, open_browser: bool = True):
    """Return an authenticated Gmail API service, refreshing/minting token.json.

    Reuses ``token_path`` if valid; refreshes it silently if expired; otherwise
    runs the one-time browser consent and caches the result.
    """  # pragma: no cover - live OAuth
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if Path(token_path).is_file():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0, open_browser=open_browser)
        Path(token_path).write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)
