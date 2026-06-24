"""Tests for the analysis experiment helpers (fast, deterministic)."""

from __future__ import annotations

from robocop_mcp.constants import Role
from robocop_mcp.domain.models import MatchRules
from robocop_mcp.learning.experiments import (
    eval_stats,
    heuristic_pick,
    visibility_coverage,
)
from robocop_mcp.learning.sensitivity import q_vs_heuristic, sensitivity_oat


def _rules(cfg, n=4):
    g = dict(cfg)
    g["grid_size"] = [n, n]
    return MatchRules.from_config(g)


def test_eval_stats_ranges(base_game_config) -> None:
    rules = _rules(base_game_config, 4)
    stats = eval_stats(rules, heuristic_pick, heuristic_pick, n=20, seed=1)
    assert 0.0 <= stats["cop_win_rate"] <= 1.0
    assert stats["avg_moves"] > 0
    # On an open board the heuristic cop reliably captures the heuristic thief.
    assert stats["cop_win_rate"] > 0.5


def test_heuristic_pick_returns_valid(base_game_config) -> None:
    from robocop_mcp.constants import MOVE_DIRECTIONS
    from robocop_mcp.domain.engine import GameEngine

    eng = GameEngine(_rules(base_game_config, 4))
    assert heuristic_pick(Role.COP, eng) in {d.value for d in MOVE_DIRECTIONS}


def test_visibility_coverage_monotonic() -> None:
    r1 = visibility_coverage(5, 5, 1)
    r2 = visibility_coverage(5, 5, 2)
    assert 0.0 < r1 < r2 <= 1.0


def test_q_vs_heuristic_keys(base_game_config) -> None:
    rules = _rules(base_game_config, 4)
    out = q_vs_heuristic(rules, base_game_config["q_learning"], episodes=120, n_eval=20)
    assert set(out) == {"q", "heuristic", "history"}
    assert 0.0 <= out["q"]["cop_win_rate"] <= 1.0
    assert len(out["history"]) == 120


def test_sensitivity_oat_grid(base_game_config) -> None:
    res = sensitivity_oat("grid_size", [3, 4], base_game_config,
                          base_game_config["q_learning"], episodes=80, n_eval=15)
    assert set(res) == {3, 4}
    assert all("cop_win_rate" in v for v in res.values())


def test_rules_for_each_param(base_game_config) -> None:
    from robocop_mcp.learning.sensitivity import _rules_for

    rules, qover = _rules_for("epsilon", 0.5, base_game_config)
    assert qover == {"epsilon": 0.5}
    rules, _ = _rules_for("grid_size", 6, base_game_config)
    assert rules.grid_width == 6 and rules.grid_height == 6
    rules, _ = _rules_for("max_barriers", 9, base_game_config)
    assert rules.max_barriers == 9
