"""Interop finalization — gated bonus report + email (NEVER auto-send).

After 6 valid sub-games we: build ``report_bonus.json`` (exact assignment §18.6
schema), print its SHA-256, and compare it with the opponent via
``confirm_final_report``. The email is sent **only** on explicit manual
confirmation (``send=True`` / ``--send``) AND only if the hashes match. The
default is **dry-run**: write the JSON-only email body to a file and send nothing.

The comparable hash is computed over the report WITHOUT ``mutual_agreement`` (that
flag is the *result* of agreeing, so it cannot be part of the agreed hash —
documented default, flagged in INTEROP_STATUS.md).
"""

from __future__ import annotations

import json
from pathlib import Path

from ..constants import GITHUB_REPO, GROUP_CODE, STUDENTS
from .hashing import hash_payload
from .session import MatchSession


def _totals_by_group(session: MatchSession) -> dict:
    """Accumulate per-team totals using the A=Cop(1-3)/Robber(4-6) schedule."""
    team_a = session.team_a
    team_b = session.opponent_team if team_a == session.our_team else session.our_team
    totals = {team_a: 0, team_b: 0}
    for r in session.results:
        a_is_cop = r["sub_game_index"] <= 3
        sc = r["scores"]
        totals[team_a] += sc["cop"] if a_is_cop else sc["robber"]
        totals[team_b] += sc["robber"] if a_is_cop else sc["cop"]
    return totals


def _bonus_claim(totals: dict) -> dict:
    """10 to the higher score, 7 to the lower, 5/5 on a draw (their §19.3)."""
    (n1, s1), (n2, s2) = totals.items()
    if s1 == s2:
        return {n1: 5, n2: 5}
    return {n1: 10, n2: 7} if s1 > s2 else {n1: 7, n2: 10}


def build_bonus_report(session: MatchSession, match_info: dict,
                       mutual_agreement: bool = False) -> dict:
    """Assemble the inter-group bonus report (assignment §18.6 schema)."""
    totals = _totals_by_group(session)
    return {
        "report_type": "bonus_game",
        "groups": {"group_1": GROUP_CODE, "group_2": session.opponent_team},
        "github_repo_group_1": GITHUB_REPO,
        "github_repo_group_2": match_info.get("their_repo", ""),
        "mcp_url_group_1_cop": match_info.get("our_cop_url", ""),
        "mcp_url_group_1_thief": match_info.get("our_thief_url", ""),
        "mcp_url_group_2_cop": match_info.get("their_cop_url", ""),
        "mcp_url_group_2_thief": match_info.get("their_thief_url", ""),
        "timezone": "Asia/Jerusalem",
        "students_group_1": [dict(s) for s in STUDENTS],
        "students_group_2": match_info.get("their_students", []),
        "ruleset_name": "cop-robber-grid-v1", "ruleset_hash": session.ruleset_hash,
        "role_schedule": {"sub_games_1_to_3": {"team_a": "cop", "team_b": "robber"},
                          "sub_games_4_to_6": {"team_a": "robber", "team_b": "cop"}},
        "seed_protocol": "commit_reveal",
        "sub_games": session.results,
        "totals_by_group": totals,
        "bonus_claim": _bonus_claim(totals),
        "mutual_agreement": mutual_agreement,
    }


def comparable_hash(report: dict) -> str:
    """SHA-256 of the report EXCLUDING ``mutual_agreement`` (the agreed-on hash)."""
    return hash_payload({k: v for k, v in report.items() if k != "mutual_agreement"})


def finalize(session: MatchSession, match_info: dict, out_dir: Path, *,
             send: bool = False, opponent_report_hash: str | None = None,
             gmail_send=None, recipient: str = "rmisegal+uoh26b@gmail.com") -> dict:
    """Save report + print hash; email ONLY if ``send`` AND hashes match."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    report = build_bonus_report(session, match_info)
    digest = comparable_hash(report)
    session.final_hash = digest  # so confirm_final_report can compare opponent vs ours
    if opponent_report_hash is None:
        opponent_report_hash = session.opponent_report_hash
    hashes_match = opponent_report_hash is not None and opponent_report_hash == digest
    report["mutual_agreement"] = hashes_match
    body = json.dumps(report, indent=2, ensure_ascii=False)
    (out / "report_bonus.json").write_text(body)
    print(f"report_bonus.json SHA256: {digest}")
    print(f"opponent hash: {opponent_report_hash} -> hashes_match={hashes_match}")

    if send and hashes_match and gmail_send is not None:
        gmail_send(report, recipient)
        status, sent = "sent", True
    else:
        (out / "email_body.txt").write_text(body)  # dry-run: write, do not send
        status = "sent" if not send else ("blocked_hash_mismatch" if not hashes_match
                                          else "blocked_no_gmail")
        status = "dry_run" if not send else status
        sent = False
    return {"report_path": str(out / "report_bonus.json"), "hash": digest,
            "hashes_match": hashes_match, "sent": sent, "status": status}
