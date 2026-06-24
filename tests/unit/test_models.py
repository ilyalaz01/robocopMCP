"""Tests for domain dataclasses (Position, MatchRules)."""

from __future__ import annotations

from robocop_mcp.constants import Outcome, Role
from robocop_mcp.domain.models import GameState, MatchRules, Position


def test_position_translate_and_tuple() -> None:
    p = Position(2, 3)
    assert p.translate(1, -1) == Position(3, 2)
    assert p.as_tuple() == (2, 3)


def test_position_chebyshev() -> None:
    assert Position(0, 0).chebyshev(Position(2, 1)) == 2
    assert Position(1, 1).chebyshev(Position(1, 1)) == 0


def test_matchrules_from_config(base_game_config: dict) -> None:
    r = MatchRules.from_config(base_game_config)
    assert r.grid_width == 5 and r.grid_height == 5
    assert r.cop_win == 20 and r.thief_win == 10
    assert r.cop_start == Position(0, 0)
    assert r.thief_start == Position(4, 4)
    assert r.num_cops == 1


def test_matchrules_overrides(base_game_config: dict) -> None:
    r = MatchRules.from_config(base_game_config).with_overrides(max_barriers=7)
    assert r.max_barriers == 7
    assert r.grid_width == 5  # unchanged


def test_gamestate_terminal_flag() -> None:
    s = GameState(cop=Position(0, 0), thief=Position(1, 1))
    assert not s.is_terminal()
    assert s.turn is Role.THIEF
    s.outcome = Outcome.COP_WIN
    assert s.is_terminal()
