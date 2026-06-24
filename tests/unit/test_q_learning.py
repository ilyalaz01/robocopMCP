"""Tests for the tabular Q-learning core (action space, encoding, Bellman, IO)."""

from __future__ import annotations

import numpy as np

from robocop_mcp.constants import PLACE_BARRIER, Role
from robocop_mcp.domain.models import Position
from robocop_mcp.learning.q_learning import QTable, action_space, encode_state


def test_action_space_per_role() -> None:
    cop = action_space(Role.COP)
    thief = action_space(Role.THIEF)
    assert len(cop) == 9 and PLACE_BARRIER in cop
    assert len(thief) == 8 and PLACE_BARRIER not in thief


def test_encode_state_clamps() -> None:
    assert encode_state(Position(0, 0), Position(2, 3)) == (2, 3)
    assert encode_state(Position(0, 0), Position(9, 9), clamp=4) == (4, 4)
    assert encode_state(Position(9, 9), Position(0, 0), clamp=4) == (-4, -4)


def test_bellman_update_known_value() -> None:
    table = QTable(["A", "B"], alpha=0.5, gamma=0.9)
    table.row((1, 0))  # ensure state exists
    table.q[(0, 0)] = np.array([10.0, 4.0])  # max next = 10
    table.update((1, 0), a=0, reward=2.0, s_next=(0, 0))
    # Q(s,a)=0; target = 2 + 0.9*10 = 11; new = 0 + 0.5*(11-0) = 5.5
    assert table.row((1, 0))[0] == 5.5


def test_select_greedy_masks_illegal() -> None:
    table = QTable(["A", "B", "C"], epsilon=0.0)
    table.q[(0, 0)] = np.array([5.0, 9.0, 1.0])
    # Best overall is index 1, but if only [0, 2] legal it must pick 0.
    assert table.select((0, 0), legal=[0, 2]) == 0
    assert table.select((0, 0), legal=[0, 1, 2]) == 1


def test_select_empty_legal_returns_zero() -> None:
    assert QTable(["A"]).select((0, 0), legal=[]) == 0


def test_decay_floor() -> None:
    table = QTable(["A"], epsilon=0.02, epsilon_decay=0.5, min_epsilon=0.01)
    table.decay()
    assert table.epsilon == 0.01  # floored
    table.decay()
    assert table.epsilon == 0.01


def test_save_load_roundtrip(tmp_path) -> None:
    table = QTable(["A", "B"], alpha=0.3)
    table.q[(1, -2)] = np.array([1.5, -0.5])
    path = tmp_path / "qt.json"
    table.save(path)
    loaded = QTable.load(path)
    assert loaded.actions == ["A", "B"]
    assert np.allclose(loaded.row((1, -2)), [1.5, -0.5])
