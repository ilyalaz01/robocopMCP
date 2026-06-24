"""Experiment helpers for the analysis notebook (rubric §8 + §10).

Provides the data behind the notebook's figures: learning curves, a Q-vs-heuristic
comparison, one-at-a-time parameter sensitivity, and observability coverage. Kept
in the package (not the notebook) so the logic is unit-tested and the notebook
cells stay short and reliable.
"""

from __future__ import annotations

import numpy as np

from ..agents.strategy import heuristic_action
from ..constants import Role
from ..domain.engine import GameEngine
from ..domain.models import MatchRules, Position
from .q_learning import QTable, action_space, encode_state
from .trainer import _apply, legal_indices


def heuristic_pick(role: Role, engine: GameEngine) -> str | None:
    """Greedy heuristic action name using the true opponent position."""
    own = engine.state.cop if role is Role.COP else engine.state.thief
    target = engine.state.thief if role is Role.COP else engine.state.cop
    action = heuristic_action(role, own, target, engine.board, engine.state.barriers)
    return action.value if action else None


def q_pick(table: QTable, role: Role, engine: GameEngine) -> str | None:
    """Greedy Q-table action name (legal-masked)."""
    own = engine.state.cop if role is Role.COP else engine.state.thief
    target = engine.state.thief if role is Role.COP else engine.state.cop
    legal = legal_indices(engine, role, table.actions)
    if not legal:
        return None
    idx = table.select(encode_state(own, target), legal, explore=False)
    return table.actions[idx]


def _apply_name(engine: GameEngine, role: Role, name: str | None) -> None:
    if name is None:
        return
    acts = action_space(role)
    _apply(engine, role, acts, acts.index(name))


def rollout(rules: MatchRules, cop_pick, thief_pick, rng) -> tuple[str, int]:
    """Play one episode from a random start; return (outcome, moves)."""
    eng = GameEngine(rules)
    w, h = rules.grid_width, rules.grid_height
    cop = Position(int(rng.integers(w)), int(rng.integers(h)))
    thief = Position(int(rng.integers(w)), int(rng.integers(h)))
    while thief == cop:
        thief = Position(int(rng.integers(w)), int(rng.integers(h)))
    eng.reset(cop=cop, thief=thief)
    while not eng.state.is_terminal():
        role = eng.state.turn
        pick = cop_pick if role is Role.COP else thief_pick
        _apply_name(eng, role, pick(role, eng))
        if eng.state.move_count > rules.max_moves:
            break
    return eng.state.outcome.value, eng.state.move_count


def eval_stats(rules: MatchRules, cop_pick, thief_pick, n: int = 50, seed: int = 1) -> dict:
    """Average cop win-rate and capture time over ``n`` rollouts."""
    rng = np.random.default_rng(seed)
    wins, moves = 0, []
    for _ in range(n):
        outcome, m = rollout(rules, cop_pick, thief_pick, rng)
        wins += outcome == "cop_win"
        moves.append(m)
    return {"cop_win_rate": wins / n, "avg_moves": float(np.mean(moves))}


def visibility_coverage(width: int, height: int, radius: int) -> float:
    """Fraction of ordered cell-pairs where the opponent is within ``radius``.

    A clean one-at-a-time sensitivity of the *observation* model: larger radius
    means the agents rely less on language to locate each other.
    """
    cells = [(x, y) for x in range(width) for y in range(height)]
    seen = total = 0
    for ax, ay in cells:
        for bx, by in cells:
            if (ax, ay) == (bx, by):
                continue
            total += 1
            seen += max(abs(ax - bx), abs(ay - by)) <= radius
    return seen / total if total else 0.0
