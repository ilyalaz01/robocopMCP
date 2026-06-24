"""Tests for the heuristic movement baseline."""

from __future__ import annotations

from robocop_mcp.agents.strategy import default_target, heuristic_action
from robocop_mcp.constants import Role
from robocop_mcp.domain.board import Board
from robocop_mcp.domain.models import Position


def test_cop_moves_toward_target() -> None:
    board = Board(5, 5)
    action = heuristic_action(Role.COP, Position(0, 0), Position(4, 4), board, set())
    # Greedy pursuit from (0,0) toward (4,4) → diagonal NE.
    assert board.step(Position(0, 0), action).chebyshev(Position(4, 4)) == 3


def test_thief_moves_away_from_target() -> None:
    board = Board(5, 5)
    action = heuristic_action(Role.THIEF, Position(2, 2), Position(2, 2), board, set())
    # Thief maximises distance and may never STAY.
    assert board.step(Position(2, 2), action).chebyshev(Position(2, 2)) == 1
    assert action.value != "STAY"


def test_returns_none_when_boxed_in() -> None:
    board = Board(1, 1)  # single cell, no legal move off it
    assert heuristic_action(Role.THIEF, Position(0, 0), Position(0, 0), board, set()) is None


def test_default_target() -> None:
    cop_start, thief_start = Position(0, 0), Position(4, 4)
    assert default_target(Role.COP, cop_start, thief_start) == thief_start
    assert default_target(Role.THIEF, cop_start, thief_start) == cop_start
