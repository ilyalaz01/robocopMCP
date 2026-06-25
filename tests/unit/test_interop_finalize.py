"""Tests for interop finalization — gated email (never auto-send)."""

from __future__ import annotations

from robocop_mcp.interop.finalize import build_bonus_report, comparable_hash, finalize
from robocop_mcp.interop.peer_tools import PeerToolService
from robocop_mcp.interop.session import MatchSession

MATCH_INFO = {"their_repo": "gh-b", "their_cop_url": "c2", "their_thief_url": "t2",
              "their_students": []}


def _session_with_results() -> MatchSession:
    s = MatchSession("il-nv-ai")
    s.set_opponent("team-beta")  # team_a = il-nv-ai (lexicographically smaller)
    outcomes = [("cop_capture", "cop", 20, 5), ("round_limit_reached", "robber", 5, 10),
                ("cop_capture", "cop", 20, 5), ("cop_capture", "cop", 20, 5),
                ("round_limit_reached", "robber", 5, 10), ("cop_capture", "cop", 20, 5)]
    for i, (code, winner, cs, rs) in enumerate(outcomes, start=1):
        s.sub_game_result(i, code, winner, cs, rs)
    return s


def test_bonus_report_schema_and_totals() -> None:
    s = _session_with_results()
    report = build_bonus_report(s, MATCH_INFO)
    assert report["report_type"] == "bonus_game"
    assert report["ruleset_name"] == "cop-robber-grid-v1"
    assert set(report["totals_by_group"]) == {"il-nv-ai", "team-beta"}
    assert "bonus_claim" in report and len(report["sub_games"]) == 6


def test_comparable_hash_excludes_mutual_agreement() -> None:
    s = _session_with_results()
    report = build_bonus_report(s, MATCH_INFO, mutual_agreement=False)
    h_false = comparable_hash(report)
    report["mutual_agreement"] = True
    assert comparable_hash(report) == h_false  # flag does not affect the agreed hash


def test_default_is_dry_run_no_send(tmp_path, capsys) -> None:
    s = _session_with_results()
    sent = []
    res = finalize(s, MATCH_INFO, tmp_path, gmail_send=lambda r, to: sent.append(to))
    assert res["status"] == "dry_run" and res["sent"] is False
    assert not sent  # nothing emailed
    assert (tmp_path / "report_bonus.json").is_file()
    assert (tmp_path / "email_body.txt").is_file()
    assert res["hash"] in capsys.readouterr().out  # SHA256 printed


def test_send_blocked_on_hash_mismatch(tmp_path) -> None:
    s = _session_with_results()
    sent = []
    res = finalize(s, MATCH_INFO, tmp_path, send=True, opponent_report_hash="sha256:nope",
                   gmail_send=lambda r, to: sent.append(to))
    assert res["status"] == "blocked_hash_mismatch" and res["sent"] is False
    assert not sent  # refused to send on mismatch


def test_send_only_when_flag_and_hash_match(tmp_path) -> None:
    s = _session_with_results()
    our_hash = finalize(s, MATCH_INFO, tmp_path)["hash"]  # dry-run to learn the hash
    sent = []
    res = finalize(s, MATCH_INFO, tmp_path, send=True, opponent_report_hash=our_hash,
                   gmail_send=lambda r, to: sent.append((to, r["mutual_agreement"])))
    assert res["status"] == "sent" and res["sent"] is True and res["hashes_match"] is True
    assert sent == [("rmisegal+uoh26b@gmail.com", True)]  # sent once, mutual_agreement=true


def test_confirm_final_report_tool_compares_hashes(tmp_path) -> None:
    s = _session_with_results()
    svc = PeerToolService(s, "tok")
    our_hash = finalize(s, MATCH_INFO, tmp_path)["hash"]  # sets s.final_hash
    assert svc.confirm_final_report("tok", our_hash)["match"] is True
    assert svc.confirm_final_report("tok", "sha256:other")["match"] is False
    # The interop send tool never actually sends.
    assert svc.send_final_report_email("tok", {})["sent"] is False
