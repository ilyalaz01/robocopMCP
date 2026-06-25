"""Send the internal JSON report for real via Gmail (Phase 11 live step).

Builds the report from a quick heuristic series (no API cost), runs the Gmail OAuth
flow (one-time browser consent → token.json), and sends with dry_run=False. The
email body is JSON only. Recipient comes from config. Run::

    uv run python scripts/send_report.py
"""

from __future__ import annotations

import json

from robocop_mcp.reporting.gmail_auth import find_client_secret
from robocop_mcp.sdk.sdk import MarlSDK


def main() -> None:
    sdk = MarlSDK()
    root = sdk.cfg.root
    recipient = sdk.cfg.get("report", "recipient_email", default="")

    series = sdk.run_series(match_id="email_send")  # heuristic, free, 6 valid sub-games
    report = sdk.build_internal_report(series)

    creds = find_client_secret(root)
    token = root / "token.json"
    print(f"OAuth client: {creds.name}\nRecipient (from config): {recipient}")
    print("Opening Gmail consent — authorize in the browser if prompted ...")

    from robocop_mcp.reporting.gmail_auth import build_gmail_service
    # open_browser=False: the only URL in play is the one we print (avoids stale tabs).
    service = build_gmail_service(creds, token, open_browser=False)

    result = sdk.send_report(series, report=report, dry_run=False,
                             service_factory=lambda: service)
    # gmail.send is least-privilege (no read scope), so we confirm from the send
    # response: a message_id means Gmail accepted + sent it, addressed to the
    # config recipient we placed in the To header.
    print("SEND RESULT:", json.dumps(result))
    if result.get("sent") and result.get("message_id"):
        print(f"CONFIRMED: email SENT to {recipient} (Gmail message id "
              f"{result['message_id']}).")
    else:
        print("WARNING: send did not return a message id — check the logs.")


if __name__ == "__main__":
    main()
