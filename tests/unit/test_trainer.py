"""Tests for the self-play trainer — legality, episode, convergence, persistence."""

from __future__ import annotations

import numpy as np

from robocop_mcp.constants import Outcome, Role
from robocop_mcp.domain.engine import GameEngine
from robocop_mcp.domain.models import MatchRules, Position
from robocop_mcp.learning.q_learning import QTable, action_space
from robocop_mcp.learning.trainer import legal_indices, run_episode, train


def _rules(cfg: dict, n: int = 4) -> MatchRules:
    g = dict(cfg)
    g["grid_size"] = [n, n]
    return MatchRules.from_config(g)


def test_legal_indices_corner(base_game_config) -> None:
    rules = _rules(base_game_config, 3)
    eng = GameEngine(rules)
    eng.reset(cop=Position(2, 2), thief=Position(0, 0))
    acts = action_space(Role.THIEF)
    legal = legal_indices(eng, Role.THIEF, acts)
    # From corner (0,0): only N, NE, E are on-board.
    assert {acts[i] for i in legal} == {"N", "NE", "E"}


def test_run_episode_terminates(base_game_config) -> None:
    rules = _rules(base_game_config, 4)
    cfg = base_game_config["q_learning"]
    rng = np.random.default_rng(0)
    tables = {r: QTable(action_space(r), rng=rng) for r in (Role.COP, Role.THIEF)}
    acts = {r: action_space(r) for r in (Role.COP, Role.THIEF)}
    eng = GameEngine(rules)
    cop_r, thief_r = run_episode(eng, tables, acts, cfg, rng)
    assert isinstance(cop_r, float) and isinstance(thief_r, float)
    assert eng.state.outcome in (Outcome.COP_WIN, Outcome.THIEF_WIN)


def test_training_improves_cop_reward(base_game_config) -> None:
    rules = _rules(base_game_config, 4)
    cfg = base_game_config["q_learning"]
    _, _, history = train(rules, cfg, episodes=400, seed=0)
    h = np.array(history)
    q = len(h) // 4
    # Deterministic (seed=0): the Cop's mean reward rises from first to last quarter.
    assert h[-q:, 0].mean() > h[:q, 0].mean()


def test_train_persists_tables(base_game_config, tmp_path) -> None:
    rules = _rules(base_game_config, 4)
    cfg = base_game_config["q_learning"]
    cop_q, thief_q, _ = train(rules, cfg, episodes=50, seed=1, out_dir=tmp_path)
    assert (tmp_path / "qtable_cop.json").is_file()
    assert (tmp_path / "qtable_thief.json").is_file()
    assert (tmp_path / "learning_curve.csv").is_file()
    assert len(cop_q.q) > 0 and len(thief_q.q) > 0
