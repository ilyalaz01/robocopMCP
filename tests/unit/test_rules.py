"""Tests for win/capture/scoring rules and move legality."""

from __future__ import annotations

import pytest

from robocop_mcp.constants import Direction, Outcome, Role
from robocop_mcp.domain.board import Board
from robocop_mcp.domain.models import GameState, MatchRules, Position
from robocop_mcp.domain.rules import (
    accumulate,
    can_place_barrier,
    is_capture,
    score_subgame,
    validate_move,
)


@pytest.fixture
def rules(base_game_config: dict) -> MatchRules:
    return MatchRules.from_config(base_game_config)


def test_is_capture(rules: MatchRules) -> None:
    assert is_capture(GameState(cop=Position(2, 2), thief=Position(2, 2)))
    assert not is_capture(GameState(cop=Position(2, 2), thief=Position(2, 3)))


def test_validate_move_ok(rules: MatchRules) -> None:
    b = Board(5, 5)
    state = GameState(cop=Position(2, 2), thief=Position(0, 0))
    ok, why, dest = validate_move(b, state, Role.COP, Direction.N, rules)
    assert ok and dest == Position(2, 3) and why == "ok"


def test_validate_move_offboard(rules: MatchRules) -> None:
    b = Board(5, 5)
    state = GameState(cop=Position(0, 0), thief=Position(4, 4))
    ok, why, _ = validate_move(b, state, Role.COP, Direction.S, rules)
    assert not ok and "off_board" in why


def test_thief_cannot_stay(rules: MatchRules) -> None:
    b = Board(5, 5)
    state = GameState(cop=Position(0, 0), thief=Position(2, 2))
    ok, why, _ = validate_move(b, state, Role.THIEF, Direction.STAY, rules)
    assert not ok and "thief_must_evade" in why


def test_cop_may_stay(rules: MatchRules) -> None:
    b = Board(5, 5)
    state = GameState(cop=Position(2, 2), thief=Position(0, 0))
    ok, why, dest = validate_move(b, state, Role.COP, Direction.STAY, rules)
    assert ok and dest == Position(2, 2)


def test_thief_blocked_by_barrier(rules: MatchRules) -> None:
    b = Board(5, 5)
    state = GameState(cop=Position(0, 0), thief=Position(2, 2))
    state.barriers = {Position(2, 3)}
    ok, why, _ = validate_move(b, state, Role.THIEF, Direction.N, rules)
    assert not ok and "barrier_block" in why


def test_barrier_existing_cell_rejected(base_game_config: dict) -> None:
    rules = MatchRules.from_config(base_game_config).with_overrides(max_barriers=5)
    state = GameState(cop=Position(1, 1), thief=Position(4, 4))
    assert can_place_barrier(state, rules)[0]
    state.barriers = {Position(1, 1)}
    ok, why = can_place_barrier(state, rules)
    assert not ok and "barrier_exists" in why


def test_barrier_limit_rejected(base_game_config: dict) -> None:
    rules = MatchRules.from_config(base_game_config).with_overrides(max_barriers=1)
    state = GameState(cop=Position(2, 2), thief=Position(4, 4))
    state.barriers = {Position(0, 0)}  # cap already reached elsewhere
    ok, why = can_place_barrier(state, rules)
    assert not ok and "barrier_limit" in why


def test_scoring(rules: MatchRules) -> None:
    assert score_subgame(Outcome.COP_WIN, rules) == (20, 5)
    assert score_subgame(Outcome.THIEF_WIN, rules) == (5, 10)
    assert score_subgame(Outcome.VOID, rules) == (0, 0)


def test_accumulate() -> None:
    totals = accumulate([(20, 5), (5, 10), (20, 5)])
    assert totals == {"cop": 45, "thief": 20}
