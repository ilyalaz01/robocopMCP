"""Self-play trainer — offline Q-table learning, no LLM and no network (SPEC §9).

Runs episodes on the pure :class:`GameEngine`, randomising start cells for state
coverage, and trains *separate* Cop and Thief tables with shaped rewards (the Cop
is pressured to capture quickly; the Thief is rewarded for surviving to timeout).
Saves both tables and the reward-per-episode curve to ``results/`` for the
learning-curve graphs.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ..constants import PLACE_BARRIER, Direction, Outcome, Role
from ..domain.engine import GameEngine
from ..domain.models import MatchRules, Position
from ..domain.rules import can_place_barrier
from .q_learning import QTable, action_space, encode_state


def _own_target(engine: GameEngine, role: Role) -> tuple[Position, Position]:
    """Return ``(own, target)`` positions for ``role`` (target = opponent)."""
    if role is Role.COP:
        return engine.state.cop, engine.state.thief
    return engine.state.thief, engine.state.cop


def legal_indices(engine: GameEngine, role: Role, actions: list[str]) -> list[int]:
    """Indices of currently-legal actions for ``role`` (mirrors engine validation)."""
    own, _ = _own_target(engine, role)
    out: list[int] = []
    for i, name in enumerate(actions):
        if name == PLACE_BARRIER:
            if can_place_barrier(engine.state, engine.rules)[0]:
                out.append(i)
        elif engine.board.is_passable(
            engine.board.step(own, Direction(name)), engine.state.barriers,
            for_thief=role is Role.THIEF,
        ):
            out.append(i)
    return out


def _apply(engine: GameEngine, role: Role, actions: list[str], idx: int):
    """Apply the chosen action index via the engine."""
    name = actions[idx]
    if name == PLACE_BARRIER:
        return engine.place_barrier(role)
    return engine.apply_move(role, Direction(name))


def _reward(role: Role, outcome: Outcome, cfg: dict) -> float:
    """Shaped per-step reward (magnitudes from ``config.q_learning``)."""
    if role is Role.COP:
        r = cfg["step_penalty"]
        return r + cfg["capture_reward"] if outcome is Outcome.COP_WIN else r
    r = cfg["survive_reward"]
    if outcome is Outcome.COP_WIN:
        return r - cfg["capture_reward"]
    if outcome is Outcome.THIEF_WIN:
        return r + cfg["capture_reward"]
    return r


def run_episode(engine: GameEngine, tables: dict, acts: dict, cfg: dict, rng) -> tuple[float, float]:
    """Play one self-play episode, updating both tables; return total rewards."""
    w, h = engine.rules.grid_width, engine.rules.grid_height
    cop = Position(int(rng.integers(w)), int(rng.integers(h)))
    thief = Position(int(rng.integers(w)), int(rng.integers(h)))
    while thief == cop:
        thief = Position(int(rng.integers(w)), int(rng.integers(h)))
    engine.reset(cop=cop, thief=thief)

    totals = {Role.COP: 0.0, Role.THIEF: 0.0}
    for _ in range(engine.rules.max_moves + 1):
        if engine.state.is_terminal():
            break
        role = engine.state.turn
        own, target = _own_target(engine, role)
        s = encode_state(own, target)
        legal = legal_indices(engine, role, acts[role])
        a = tables[role].select(s, legal)
        _apply(engine, role, acts[role], a)
        reward = _reward(role, engine.state.outcome, cfg)
        own_next, target_next = _own_target(engine, role)
        tables[role].update(s, a, reward, encode_state(own_next, target_next))
        totals[role] += reward
    return totals[Role.COP], totals[Role.THIEF]


def train(rules: MatchRules, cfg: dict, episodes: int, seed: int = 0, out_dir: Path | None = None):
    """Train Cop + Thief tables over ``episodes`` self-play games.

    Returns ``(cop_table, thief_table, history)`` where history is a list of
    ``(cop_reward, thief_reward)`` per episode. Persists tables + curve if
    ``out_dir`` is given.
    """
    rng = np.random.default_rng(seed)
    acts = {Role.COP: action_space(Role.COP), Role.THIEF: action_space(Role.THIEF)}
    qp = cfg
    tables = {
        role: QTable(acts[role], qp["alpha"], qp["gamma"], qp["epsilon"],
                     qp["epsilon_decay"], qp["min_epsilon"], rng)
        for role in (Role.COP, Role.THIEF)
    }
    engine = GameEngine(rules)
    history: list[tuple[float, float]] = []
    for _ in range(episodes):
        history.append(run_episode(engine, tables, acts, cfg, rng))
        tables[Role.COP].decay()
        tables[Role.THIEF].decay()

    if out_dir is not None:
        out = Path(out_dir)
        tables[Role.COP].save(out / "qtable_cop.json")
        tables[Role.THIEF].save(out / "qtable_thief.json")
        np.savetxt(out / "learning_curve.csv", np.array(history), delimiter=",",
                   header="cop_reward,thief_reward", comments="")
    return tables[Role.COP], tables[Role.THIEF], history
