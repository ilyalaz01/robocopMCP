"""Reporting concern for the SDK — build reports + trigger the Cop's email.

Mixed into :class:`~robocop_mcp.sdk.sdk.MarlSDK`; relies on the host providing
``cfg``, ``jsonl``, and ``rules``. One concern only (rubric §3.2): turn a series
result into the exact-schema JSON and send it (dry-run tonight).
"""

from __future__ import annotations

from pathlib import Path

from ..reporting.gmail_client import GmailClient
from ..reporting.report_builder import (
    build_bonus_report,
    build_internal_report,
    count_valid,
    mcp_url,
)
from ..shared.gatekeeper import ApiGatekeeper
from ..shared.logging_setup import log_event


class ReportingMixin:
    """Adds report-building and email-triggering to the SDK."""

    def _server_urls(self) -> tuple[str, str]:
        servers = self.cfg.get("servers", default={})  # type: ignore[attr-defined]
        return (mcp_url(servers["cop_host"], servers["cop_port"]),
                mcp_url(servers["thief_host"], servers["thief_port"]))

    def build_internal_report(self, series) -> dict:
        """Build the mandatory single-group report from a series result."""
        cop_url, thief_url = self._server_urls()
        return build_internal_report(series, self.cfg, cop_url, thief_url)  # type: ignore[attr-defined]

    def build_bonus_report(self, series, opponent: dict, mutual_agreement: dict,
                           bonus_claim: bool = True) -> dict:
        """Build the inter-group bonus report (group_2 details from Ilya)."""
        return build_bonus_report(series, self.cfg, opponent, mutual_agreement, bonus_claim)  # type: ignore[attr-defined]

    def send_report(self, series, report: dict | None = None, dry_run: bool = True,
                    out_dir: Path | None = None) -> dict:
        """Cop emails the JSON report — only once all sub-games are valid (SPEC §11)."""
        valid = count_valid(series)
        needed = self.rules.num_games  # type: ignore[attr-defined]
        if valid < needed:
            log_event(self.jsonl, "email_skipped", valid=valid, needed=needed)  # type: ignore[attr-defined]
            raise ValueError(f"only {valid}/{needed} valid sub-games — Cop will not email")
        report = report or self.build_internal_report(series)
        recipient = self.cfg.get("report", "recipient_email", default="")  # type: ignore[attr-defined]
        out = out_dir or (self.cfg.root / "results")  # type: ignore[attr-defined]
        return self._gmail_client().send(report, recipient, dry_run=dry_run, out_dir=out)

    def _gmail_client(self) -> GmailClient:
        gatekeeper = ApiGatekeeper.from_config(self.cfg, "gmail", self.jsonl)  # type: ignore[attr-defined]
        return GmailClient(gatekeeper, service_factory=None, jsonl=self.jsonl)  # type: ignore[attr-defined]
