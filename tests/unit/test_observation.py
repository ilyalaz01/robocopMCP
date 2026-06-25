"""Tests for partial observation by vision radius."""

from __future__ import annotations

from robocop_mcp.constants import Role
from robocop_mcp.domain.board import Board
from robocop_mcp.domain.models import GameState, Position
from robocop_mcp.domain.observation import build_observation, visible_cells


def test_visible_cells_radius_one_center() -> None:
    b = Board(5, 5)
    cells = visible_cells(b, Position(2, 2), 1)
    assert len(cells) == 9  # full 3x3 Moore neighbourhood
    assert Position(2, 2) in cells


def test_visible_cells_clipped_at_corner() -> None:
    b = Board(5, 5)
    cells = visible_cells(b, Position(0, 0), 1)
    assert len(cells) == 4  # corner: self + 3 neighbours


def test_opponent_hidden_outside_radius() -> None:
    b = Board(5, 5)
    state = GameState(cop=Position(0, 0), thief=Position(4, 4))
    obs = build_observation(b, state, Role.COP, radius=1)
    assert obs.opponent_pos is None
    assert obs.self_pos == Position(0, 0)
    assert obs.role is Role.COP


def test_opponent_visible_inside_radius() -> None:
    b = Board(5, 5)
    state = GameState(cop=Position(2, 2), thief=Position(3, 3))
    obs = build_observation(b, state, Role.COP, radius=1)
    assert obs.opponent_pos == (3, 3)


def test_only_visible_barriers_reported() -> None:
    b = Board(5, 5)
    state = GameState(cop=Position(2, 2), thief=Position(0, 0))
    state.barriers = {Position(2, 3), Position(0, 0)}
    obs = build_observation(b, state, Role.COP, radius=1)
    assert (2, 3) in obs.visible_barriers
    assert (0, 0) not in obs.visible_barriers  # out of the cop's window


def test_full_visibility_sees_everything() -> None:
    b = Board(5, 5)
    state = GameState(cop=Position(0, 0), thief=Position(4, 4))
    state.barriers = {Position(2, 2), Position(3, 1)}
    obs = build_observation(b, state, Role.COP, radius=1, full=True)
    # Opponent always visible, whole board visible, all barriers reported.
    assert obs.opponent_pos == (4, 4)
    assert len(obs.visible_cells) == 25
    assert set(obs.visible_barriers) == {(2, 2), (3, 1)}
