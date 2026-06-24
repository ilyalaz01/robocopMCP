"""Tests for Board geometry — bounds, steps, passability, legal moves."""

from __future__ import annotations

import pytest

from robocop_mcp.constants import Direction
from robocop_mcp.domain.board import Board
from robocop_mcp.domain.models import Position


def test_rejects_nonpositive_dims() -> None:
    with pytest.raises(ValueError, match="positive"):
        Board(0, 5)
    with pytest.raises(ValueError, match="positive"):
        Board(5, -1)


def test_in_bounds() -> None:
    b = Board(3, 3)
    assert b.in_bounds(Position(0, 0))
    assert b.in_bounds(Position(2, 2))
    assert not b.in_bounds(Position(3, 0))
    assert not b.in_bounds(Position(-1, 1))


def test_step_directions() -> None:
    b = Board(5, 5)
    assert b.step(Position(2, 2), Direction.N) == Position(2, 3)
    assert b.step(Position(2, 2), Direction.SE) == Position(3, 1)
    assert b.step(Position(2, 2), Direction.STAY) == Position(2, 2)


def test_passability_barrier_blocks_only_thief() -> None:
    b = Board(3, 3)
    barriers = {Position(1, 1)}
    assert not b.is_passable(Position(1, 1), barriers, for_thief=True)
    assert b.is_passable(Position(1, 1), barriers, for_thief=False)
    assert not b.is_passable(Position(3, 3), barriers, for_thief=False)


def test_legal_moves_corner_excludes_offboard() -> None:
    b = Board(3, 3)
    moves = b.legal_moves(Position(0, 0), set(), for_thief=True)
    # From a corner only N, NE, E are on-board.
    assert set(moves) == {Direction.N, Direction.NE, Direction.E}


def test_legal_moves_thief_avoids_barriers() -> None:
    b = Board(3, 3)
    barriers = {Position(1, 1), Position(0, 1)}
    thief_moves = b.legal_moves(Position(0, 0), barriers, for_thief=True)
    cop_moves = b.legal_moves(Position(0, 0), barriers, for_thief=False)
    assert Direction.N not in thief_moves  # (0,1) is a barrier
    assert Direction.NE not in thief_moves  # (1,1) is a barrier
    assert Direction.N in cop_moves  # cop ignores barriers


def test_all_cells_count() -> None:
    assert len(Board(4, 3).all_cells()) == 12
