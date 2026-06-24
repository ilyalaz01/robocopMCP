"""Gmail sender — code-ready; live OAuth send is Phase 11 (SPEC §11).

The Cop sends a single email whose body is **JSON only** (no prose) so the
grader's system can parse it. The send goes through the ApiGatekeeper like every
external call. Tonight the tested path is ``--dry-run``, which writes the exact
email body + report JSON to ``results/`` without sending; the live OAuth flow
(``credentials.json`` + browser consent) is left as a "DO WITH ILYA" step.
"""

from __future__ import annotations

import base64
import json
from email.mime.text import MIMEText
from pathlib import Path

from ..shared.logging_setup import log_event


def encode_message(recipient: str, subject: str, json_body: str) -> dict:
    """Build a Gmail API ``raw`` payload from a JSON-only body."""
    mime = MIMEText(json_body, "plain", "utf-8")
    mime["to"] = recipient
    mime["subject"] = subject
    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
    return {"raw": raw}


class GmailClient:
    """Sends the report email via the Gmail API, guarded by the gatekeeper.

    Setup:  gatekeeper, service_factory (builds the live Gmail service — mocked in
            tests / absent in dry-run), jsonl (event log).
    """

    def __init__(self, gatekeeper, service_factory=None, jsonl=None) -> None:
        self.gatekeeper = gatekeeper
        self.service_factory = service_factory
        self.jsonl = jsonl

    def send(self, report: dict, recipient: str, subject: str = "robocopMCP result",
             dry_run: bool = True, out_dir: Path | None = None) -> dict:
        """Send (or, in dry-run, persist) the JSON report. Body is JSON only."""
        body = json.dumps(report, indent=2, ensure_ascii=False)
        if dry_run:
            return self._dry_run(report, body, out_dir)

        payload = encode_message(recipient, subject, body)
        service = self.service_factory()
        send_call = service.users().messages().send
        result = self.gatekeeper.execute(lambda: send_call(userId="me", body=payload).execute())
        message_id = result.get("id") if isinstance(result, dict) else getattr(result, "id", None)
        log_event(self.jsonl, "email_sent", recipient=recipient, message_id=message_id)
        return {"sent": True, "message_id": message_id}

    def _dry_run(self, report: dict, body: str, out_dir: Path | None) -> dict:
        """Write the report JSON + email body to ``results/`` and log it."""
        out = Path(out_dir) if out_dir else Path("results")
        out.mkdir(parents=True, exist_ok=True)
        report_path = out / "report_internal.json"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        (out / "email_body.txt").write_text(body)
        log_event(self.jsonl, "email_dry_run", path=str(report_path))
        return {"sent": False, "dry_run": True, "report_path": str(report_path)}
