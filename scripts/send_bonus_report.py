"""Send the AGREED interop bonus report for real (live --send step).

Loads the EXACT on-disk ``results/interop/report_bonus.json`` (mutual_agreement
already set; canonical hash agreed bit-for-bit with the opponent) and emails it
JSON-only via the Gmail API through the ApiGatekeeper. Recipient comes from
``config/config_interop.json``. This does NOT rebuild the report (so the agreed
hash is preserved). Run::

    uv run python scripts/send_bonus_report.py
"""

from __future__ import annotations

import json

from robocop_mcp.reporting.gmail_auth import build_gmail_service, find_client_secret
from robocop_mcp.reporting.gmail_client import GmailClient
from robocop_mcp.shared.config import ConfigManager
from robocop_mcp.shared.gatekeeper import ApiGatekeeper
from robocop_mcp.shared.logging_setup import setup_logging


def main() -> None:  # pragma: no cover - live network send
    cfg = ConfigManager()
    report = json.loads((cfg.root / "results" / "interop" / "report_bonus.json").read_text())
    icfg = json.loads((cfg.root / "config" / "config_interop.json").read_text())
    recipient = icfg["email_report"]["recipient"]

    jsonl = setup_logging(cfg)
    service = build_gmail_service(find_client_secret(cfg.root), cfg.root / "token.json",
                                  open_browser=False)
    gatekeeper = ApiGatekeeper.from_config(cfg, "gmail", jsonl)
    result = GmailClient(gatekeeper, service_factory=lambda: service, jsonl=jsonl).send(
        report, recipient,
        subject="robocopMCP bonus_game result — il-nv-ai vs vm__fabi", dry_run=False)

    print("RECIPIENT:", recipient)
    print("mutual_agreement:", report.get("mutual_agreement"))
    print("SEND RESULT:", json.dumps(result))


if __name__ == "__main__":
    main()
