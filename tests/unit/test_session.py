"""Tests for GameSession mailbox + SessionRegistry."""

from __future__ import annotations

from robocop_mcp.constants import Role
from robocop_mcp.domain.models import MatchRules
from robocop_mcp.mcp.session import GameSession, SessionRegistry


def _rules(cfg: dict) -> MatchRules:
    return MatchRules.from_config(cfg)


def test_mailbox_read_for_returns_opponent_only(base_game_config: dict) -> None:
    s = GameSession("m1", _rules(base_game_config))
    s.post_message(Role.COP, "cop says hi")
    s.post_message(Role.THIEF, "thief replies")
    assert [m["text"] for m in s.read_for(Role.COP)] == ["thief replies"]
    assert [m["text"] for m in s.read_for(Role.THIEF)] == ["cop says hi"]


def test_read_for_limit(base_game_config: dict) -> None:
    s = GameSession("m1", _rules(base_game_config))
    for i in range(8):
        s.post_message(Role.THIEF, f"msg{i}")
    msgs = s.read_for(Role.COP, limit=3)
    assert [m["text"] for m in msgs] == ["msg5", "msg6", "msg7"]


def test_both_confirmed(base_game_config: dict) -> None:
    s = GameSession("m1", _rules(base_game_config))
    assert not s.both_confirmed()
    s.confirmations[Role.COP.value] = True
    assert not s.both_confirmed()
    s.confirmations[Role.THIEF.value] = True
    assert s.both_confirmed()


def test_registry_create_get_drop(base_game_config: dict) -> None:
    reg = SessionRegistry()
    sess = reg.create("m1", _rules(base_game_config))
    assert reg.get("m1") is sess
    assert reg.get("missing") is None
    reg.drop("m1")
    assert reg.get("m1") is None
