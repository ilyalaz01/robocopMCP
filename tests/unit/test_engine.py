"""Tests for the GameEngine state machine — incl. the SPEC §3 edge cases."""

from __future__ import annotations

import pytest

from robocop_mcp.constants import Direction, Outcome, Role
from robocop_mcp.domain.engine import GameEngine
from robocop_mcp.domain.models import MatchRules, Position


@pytest.fixture
def engine(base_game_config: dict) -> GameEngine:
    return GameEngine(MatchRules.from_config(base_game_config))


def test_thief_moves_first(engine: GameEngine) -> None:
    assert engine.state.turn is Role.THIEF
    res = engine.apply_move(Role.COP, Direction.N)
    assert not res.ok and "not_your_turn" in res.reason


def test_turn_alternates(engine: GameEngine) -> None:
    # Thief starts at (4,4); SW is on-board, NW/N/E are not.
    engine.apply_move(Role.THIEF, Direction.SW)
    assert engine.state.turn is Role.COP
    engine.apply_move(Role.COP, Direction.NE)
    assert engine.state.turn is Role.THIEF
    assert engine.state.move_count == 2


def test_capture_on_first_cop_move(base_game_config: dict) -> None:
    rules = MatchRules.from_config(base_game_config)
    eng = GameEngine(rules)
    eng.reset(cop=Position(2, 2), thief=Position(3, 2))
    eng.apply_move(Role.THIEF, Direction.N)  # thief flees to (3,3)
    res = eng.apply_move(Role.COP, Direction.NE)  # cop steps onto (3,3)
    assert res.ok
    assert eng.state.outcome is Outcome.COP_WIN


def test_timeout_is_thief_win(base_game_config: dict) -> None:
    cfg = dict(base_game_config)
    cfg["max_moves"] = 2
    eng = GameEngine(MatchRules.from_config(cfg))
    eng.reset(cop=Position(0, 0), thief=Position(4, 4))
    eng.apply_move(Role.THIEF, Direction.SW)  # ply 1 -> (3,3)
    eng.apply_move(Role.COP, Direction.N)     # ply 2 -> timeout
    assert eng.state.outcome is Outcome.THIEF_WIN
    res = eng.result(index=0)
    assert res.cop_score == 5 and res.thief_score == 10


def test_illegal_move_rejected_no_state_change(engine: GameEngine) -> None:
    before = engine.state.thief
    res = engine.apply_move(Role.THIEF, Direction.STAY)
    assert not res.ok and "thief_must_evade" in res.reason
    assert engine.state.thief == before
    assert engine.state.move_count == 0


def test_no_actions_after_game_over(base_game_config: dict) -> None:
    eng = GameEngine(MatchRules.from_config(base_game_config))
    eng.reset(cop=Position(2, 2), thief=Position(2, 3))
    eng.apply_move(Role.THIEF, Direction.E)   # thief -> (3,3)
    eng.apply_move(Role.COP, Direction.NE)    # cop -> (3,3) capture
    assert eng.state.is_terminal()
    res = eng.apply_move(Role.THIEF, Direction.N)
    assert not res.ok and "game_over" in res.reason


def test_barrier_placement_forfeits_move(base_game_config: dict) -> None:
    eng = GameEngine(MatchRules.from_config(base_game_config))
    eng.reset(cop=Position(2, 2), thief=Position(4, 4))
    eng.apply_move(Role.THIEF, Direction.SW)
    pos_before = eng.state.cop
    res = eng.place_barrier(Role.COP)
    assert res.ok and res.placed_barrier
    assert eng.state.cop == pos_before  # cop did not move
    assert pos_before in eng.state.barriers
    assert eng.state.turn is Role.THIEF  # turn still passed


def test_thief_cannot_place_barrier(engine: GameEngine) -> None:
    res = engine.place_barrier(Role.THIEF)
    assert not res.ok and "barrier_forbidden" in res.reason


def test_barrier_out_of_turn_rejected(engine: GameEngine) -> None:
    # It is the Thief's turn at the start, so the Cop cannot place a barrier.
    res = engine.place_barrier(Role.COP)
    assert not res.ok and "not_your_turn" in res.reason


def test_barrier_on_existing_rejected(base_game_config: dict) -> None:
    eng = GameEngine(MatchRules.from_config(base_game_config))
    eng.reset(cop=Position(2, 2), thief=Position(4, 4))
    eng.apply_move(Role.THIEF, Direction.SW)
    eng.place_barrier(Role.COP)
    eng.apply_move(Role.THIEF, Direction.NW)
    res = eng.place_barrier(Role.COP)  # same cell already a barrier
    assert not res.ok and "barrier_exists" in res.reason


def test_observe_and_digest(engine: GameEngine) -> None:
    obs = engine.observe(Role.COP)
    assert obs.self_pos == Position(0, 0)
    digest = engine._digest()
    assert digest["turn"] == "thief" and digest["move_count"] == 0
