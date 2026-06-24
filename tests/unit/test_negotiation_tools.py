"""Tests for the negotiation tools mixin."""

from __future__ import annotations

import pytest

from robocop_mcp.constants import Role
from robocop_mcp.domain.models import MatchRules
from robocop_mcp.mcp.session import SessionRegistry
from robocop_mcp.mcp.tools import AgentToolService

TOKEN = "t"


@pytest.fixture
def services(base_game_config: dict, tmp_path):
    reg = SessionRegistry()
    reg.create("m1", MatchRules.from_config(base_game_config))
    jsonl = tmp_path / "events.jsonl"
    return (
        AgentToolService(reg, Role.COP, TOKEN, jsonl),
        AgentToolService(reg, Role.THIEF, TOKEN, jsonl),
        reg,
    )


def test_propose_records_and_messages(services) -> None:
    cop, _, reg = services
    res = cop.negotiate_propose("m1", TOKEN, {"max_barriers": 7}, "Let's allow 7 barriers.")
    assert res["ok"]
    session = reg.get("m1")
    assert session.proposals[0]["rules"] == {"max_barriers": 7}
    assert session.mailbox[0].text.startswith("Let's allow")


def test_respond_accept_sets_agreement(services) -> None:
    cop, thief, reg = services
    cop.negotiate_propose("m1", TOKEN, {"max_barriers": 7}, "propose 7")
    res = thief.negotiate_respond("m1", TOKEN, True, {}, "agreed")
    assert res["ok"] and res["agreed_rules"] == {"max_barriers": 7}


def test_confirm_requires_both(services) -> None:
    cop, thief, _ = services
    assert not cop.negotiate_confirm("m1", TOKEN, "ready")["both_confirmed"]
    assert thief.negotiate_confirm("m1", TOKEN, "ready too")["both_confirmed"]


def test_negotiation_auth_and_no_session(services) -> None:
    cop, _, _ = services
    assert not cop.negotiate_propose("m1", "bad", {}, "x")["ok"]
    assert cop.negotiate_respond("missing", TOKEN, True, {}, "x")["error"] == "no_session"
    assert cop.negotiate_confirm("missing", TOKEN, "x")["error"] == "no_session"
