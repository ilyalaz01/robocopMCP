"""Tests for PBRS potential, escape buckets, and enriched Cop state (ADR-0004)."""

from __future__ import annotations

from robocop_mcp.domain.engine import GameEngine
from robocop_mcp.domain.models import MatchRules, Position
from robocop_mcp.learning.shaping import (
    cop_state,
    escape_bucket,
    potential,
    thief_escape_count,
)


def _engine(base_game_config) -> GameEngine:
    return GameEngine(MatchRules.from_config(base_game_config))


def test_escape_count_corner_vs_centre(base_game_config) -> None:
    eng = _engine(base_game_config)
    eng.reset(cop=Position(2, 2), thief=Position(0, 0))
    assert thief_escape_count(eng) == 3  # corner: N, NE, E
    eng.reset(cop=Position(0, 0), thief=Position(2, 2))
    assert thief_escape_count(eng) == 8  # centre: all 8


def test_barrier_reduces_escape_and_raises_potential(base_game_config) -> None:
    eng = _engine(base_game_config)
    eng.reset(cop=Position(2, 2), thief=Position(0, 0))
    before = potential(eng)
    eng.state.barriers.add(Position(1, 0))  # wall off one of the thief's escapes
    after = potential(eng)
    assert thief_escape_count(eng) == 2
    assert after > before  # Phi rises when the thief is more boxed in


def test_escape_bucket_boundaries() -> None:
    assert escape_bucket(0) == 0 and escape_bucket(2) == 0
    assert escape_bucket(3) == 1 and escape_bucket(5) == 1
    assert escape_bucket(6) == 2 and escape_bucket(8) == 2


def test_cop_state_enriched_vs_plain(base_game_config) -> None:
    eng = _engine(base_game_config)
    eng.reset(cop=Position(2, 2), thief=Position(0, 0))
    plain = cop_state(eng, enriched=False)
    enriched = cop_state(eng, enriched=True)
    assert len(plain) == 2
    assert len(enriched) == 3 and enriched[2] == 1  # plain corner → 3 escapes → bucket 1
    eng.state.barriers.add(Position(1, 0))  # wall one escape → 2 left → bucket 0
    assert cop_state(eng, enriched=True)[2] == 0
