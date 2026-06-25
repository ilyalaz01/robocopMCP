"""Finalize an interop match: save report_bonus.json + print SHA256, gated email.

NEVER auto-sends. Plays 6 self-play sub-games to populate results (stand-in for a
live opponent), builds the bonus report, prints its hash, and emails ONLY with
``--send`` AND a matching ``--opponent-hash``. Default = dry-run (writes body).

    uv run python scripts/interop_finalize.py                       # dry-run
    uv run python scripts/interop_finalize.py --opponent-hash sha256:..  # compare
    uv run python scripts/interop_finalize.py --send --opponent-hash sha256:..  # send if match
"""

from __future__ import annotations

import argparse
from pathlib import Path

from robocop_mcp.domain.models import Position
from robocop_mcp.interop.constants import TERMINAL_CODES
from robocop_mcp.interop.finalize import finalize
from robocop_mcp.interop.peer_agent import PlayerAgent, play_sub_game
from robocop_mcp.interop.session import MatchSession

STARTS = [((0, 0), (4, 4)), ((4, 0), (0, 4)), ((2, 0), (2, 4)),
          ((0, 4), (4, 0)), ((4, 4), (0, 0)), ((0, 2), (4, 2))]


def _gmail_send(report: dict, recipient: str) -> None:  # pragma: no cover - live send
    from robocop_mcp.reporting.gmail_auth import build_gmail_service, find_client_secret
    from robocop_mcp.reporting.gmail_client import GmailClient
    from robocop_mcp.shared.config import ConfigManager
    from robocop_mcp.shared.gatekeeper import ApiGatekeeper
    from robocop_mcp.shared.logging_setup import setup_logging

    cfg = ConfigManager()
    jsonl = setup_logging(cfg)
    service = build_gmail_service(find_client_secret(cfg.root), cfg.root / "token.json",
                                  open_browser=False)
    gatekeeper = ApiGatekeeper.from_config(cfg, "gmail", jsonl)
    GmailClient(gatekeeper, service_factory=lambda: service, jsonl=jsonl).send(
        report, recipient, dry_run=False)


def main() -> None:
    ap = argparse.ArgumentParser(prog="interop_finalize")
    ap.add_argument("--send", action="store_true", help="actually email (requires hash match)")
    ap.add_argument("--opponent-hash", default=None, help="opponent's report SHA256")
    args = ap.parse_args()

    session = MatchSession("il-nv-ai")
    session.set_opponent("team-beta")
    cop, rob = PlayerAgent("il-nv-ai"), PlayerAgent("team-beta")
    for i, (c, r) in enumerate(STARTS, start=1):
        code = play_sub_game(cop, rob, Position(*c), Position(*r), session.rules)
        winner = TERMINAL_CODES[code]
        cs, rs = (20, 5) if winner == "cop" else (5, 10)
        session.sub_game_result(i, code, winner, cs, rs)

    match_info = {"their_repo": "", "their_cop_url": "", "their_thief_url": "",
                  "their_students": []}
    result = finalize(session, match_info, Path("results/interop"), send=args.send,
                      opponent_report_hash=args.opponent_hash, gmail_send=_gmail_send)
    print("FINALIZE:", result)


if __name__ == "__main__":
    main()
