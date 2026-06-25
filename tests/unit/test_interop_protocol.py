"""Tests for interop bit-exact + protocol pieces (hashing, commit-reveal, tools)."""

from __future__ import annotations

from robocop_mcp.constants import Role
from robocop_mcp.interop import commit_reveal as cr
from robocop_mcp.interop.capability_handshake import (
    build_opponent_profile,
    role_for,
    team_order,
)
from robocop_mcp.interop.hashing import canonical_json, hash_payload, ruleset_hash
from robocop_mcp.interop.peer_tools import PeerToolService
from robocop_mcp.interop.session import MatchSession

TOKEN = "tok"


def test_canonical_json_is_sorted_compact() -> None:
    assert canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}'
    assert hash_payload({"a": 1}).startswith("sha256:")
    assert ruleset_hash() == ruleset_hash()  # deterministic


def test_commit_reveal_roundtrip_and_seed() -> None:
    nonce = cr.generate_nonce()
    assert cr.verify(nonce, cr.commitment(nonce))
    assert not cr.verify("wrong", cr.commitment(nonce))
    seed = cr.derive_seed("aa", "bb", 1, ruleset_hash())
    assert seed == cr.derive_seed("aa", "bb", 1, ruleset_hash())  # deterministic


def test_seed_to_positions_disjoint_and_in_bounds() -> None:
    seed = cr.derive_seed(cr.generate_nonce(), cr.generate_nonce(), 3, ruleset_hash())
    cop, rob = cr.seed_to_positions(seed, 5, 5)
    assert cop != rob
    for p in (cop, rob):
        assert 0 <= p.x < 5 and 0 <= p.y < 5


def test_team_order_and_role_schedule() -> None:
    a, b = team_order("Team-Beta", "il-nv-ai")  # lexicographically 'il-nv-ai' < 'team-beta'
    assert a == "il-nv-ai" and b == "Team-Beta"
    # Team A = Cop in sub-games 1-3, Robber in 4-6.
    assert role_for(1, "il-nv-ai", a) is Role.COP
    assert role_for(4, "il-nv-ai", a) is Role.THIEF
    assert role_for(1, "Team-Beta", a) is Role.THIEF


def test_build_profile_defaults_when_no_capabilities() -> None:
    prof = build_opponent_profile(None)
    assert prof.timeout_seconds == 60
    prof2 = build_opponent_profile({"timeout_seconds": 30, "move_template": "Go {word}."})
    assert prof2.timeout_seconds == 30 and prof2.move_template == "Go {word}."


def _service() -> PeerToolService:
    return PeerToolService(MatchSession("il-nv-ai"), TOKEN, repo_url="gh", mcp_urls={})


def test_tools_require_token() -> None:
    svc = _service()
    assert svc.get_capabilities("bad")["error"] == "unauthorized"
    assert svc.accept_ruleset("bad", "x", "y")["ok"] is False


def test_ruleset_accept_match_and_mismatch() -> None:
    svc = _service()
    good = svc.accept_ruleset(TOKEN, "cop-robber-grid-v1", ruleset_hash())
    assert good["ok"] and good["terminal"] is None
    bad = svc.accept_ruleset(TOKEN, "cop-robber-grid-v1", "sha256:deadbeef")
    assert not bad["ok"] and bad["terminal"] == "protocol_failure"


def test_commit_reveal_tools_and_capabilities() -> None:
    svc = _service()
    svc.exchange_team_identity(TOKEN, "Team-Beta")
    caps = svc.get_capabilities(TOKEN)["capabilities"]
    assert caps["role_flexible"] is True and caps["ruleset_name"] == "cop-robber-grid-v1"
    commit = svc.commit_nonce(TOKEN, 1, "sha256:opp")["our_commitment"]
    assert commit.startswith("sha256:")
