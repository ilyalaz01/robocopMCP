"""Unit tests for the default heuristic decider."""

from __future__ import annotations

from robocop_mcp.constants import Role
from robocop_mcp.orchestrator.turn_loop import default_decider


def test_decider_follows_suggestion() -> None:
    msg, (kind, direction) = default_decider(Role.COP, {"move_count": 2}, [], "NE")
    assert kind == "move" and direction == "NE"
    assert "moving NE" in msg


def test_decider_cop_boxed_places_barrier() -> None:
    _, (kind, direction) = default_decider(Role.COP, {"move_count": 5}, [], None)
    assert kind == "barrier" and direction is None


def test_decider_thief_cornered() -> None:
    msg, (kind, direction) = default_decider(Role.THIEF, {"move_count": 9}, [], None)
    assert kind == "move" and direction is None
    assert "cornered" in msg
