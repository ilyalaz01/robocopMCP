"""Tests for per-sub-game start generation (fixes the identical-games defect)."""

from __future__ import annotations

from robocop_mcp.domain.models import MatchRules, Position
from robocop_mcp.domain.starts import generate_starts


def _rules(cfg, **over) -> MatchRules:
    g = dict(cfg)
    g.update(over)
    return MatchRules.from_config(g)


def test_seeded_random_distinct_and_nonoverlapping(base_game_config) -> None:
    rules = _rules(base_game_config, start_mode="seeded_random", start_seed=42)
    starts = generate_starts(rules, 6)
    assert len(starts) == 6
    assert len({(c.as_tuple(), t.as_tuple()) for c, t in starts}) == 6  # all distinct
    assert all(c != t for c, t in starts)  # cop != thief


def test_seeded_random_reproducible(base_game_config) -> None:
    rules = _rules(base_game_config, start_mode="seeded_random", start_seed=42)
    assert generate_starts(rules, 6) == generate_starts(rules, 6)


def test_seeded_random_seed_changes_starts(base_game_config) -> None:
    a = generate_starts(_rules(base_game_config, start_mode="seeded_random", start_seed=1), 6)
    b = generate_starts(_rules(base_game_config, start_mode="seeded_random", start_seed=2), 6)
    assert a != b


def test_fixed_pairs_uses_config_table(base_game_config) -> None:
    rules = _rules(base_game_config, start_mode="fixed_pairs",
                   start_pairs=[[[0, 0], [4, 4]], [[4, 0], [0, 4]]])
    starts = generate_starts(rules, 4)
    assert starts[0] == (Position(0, 0), Position(4, 4))
    assert starts[1] == (Position(4, 0), Position(0, 4))
    assert starts[2] == starts[0]  # cycles when fewer pairs than games


def test_fixed_mode_repeats_corner(base_game_config) -> None:
    rules = _rules(base_game_config, start_mode="fixed")
    starts = generate_starts(rules, 3)
    assert len(set(starts)) == 1  # legacy behaviour: identical corner starts
