"""Tests for the barrier A/B study helpers (fast, deterministic)."""

from __future__ import annotations

from robocop_mcp.domain.models import MatchRules
from robocop_mcp.learning.ab_barriers import ab_compare, eval_cop
from robocop_mcp.learning.trainer import train


def _rules(cfg, n=5):
    g = dict(cfg)
    g["grid_size"] = [n, n]
    return MatchRules.from_config(g)


def test_eval_cop_stats_shape(base_game_config) -> None:
    rules = _rules(base_game_config)
    cop, _, _ = train(rules, base_game_config["q_learning"], episodes=80, seed=0)
    stats = eval_cop(rules, cop, enriched=False, n=20, corner=True)
    assert set(stats) == {"cop_win_rate", "avg_moves", "barrier_use_rate"}
    assert 0.0 <= stats["cop_win_rate"] <= 1.0
    assert stats["avg_moves"] > 0


def test_ab_compare_four_variants(base_game_config) -> None:
    rules = _rules(base_game_config)
    ab = ab_compare(rules, base_game_config["q_learning"], episodes=80, n_eval=15, seed=0)
    assert set(ab) == {"baseline", "shaping_only", "enrich_only", "shaping_enrich"}
    assert all("barrier_use_rate" in v for v in ab.values())
