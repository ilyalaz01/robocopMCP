"""A/B study: PBRS+enrichment vs the baseline Cop (ADR-0004, rubric §8).

Trains a baseline Cop (no shaping, plain state) and a shaped Cop (PBRS + enriched
state + corner curriculum), then measures capture rate, average capture time, and
barrier-usage frequency for each. Honest expectation on an open 5×5: PBRS is
policy-invariant, so it does not manufacture barrier use that isn't optimal — the
study quantifies that barrier use stays low and capture time is not harmed.
"""

from __future__ import annotations

import numpy as np

from ..constants import PLACE_BARRIER, Direction, Role
from ..domain.engine import GameEngine
from ..domain.models import MatchRules
from .experiments import heuristic_pick
from .shaping import cop_state
from .trainer import _corner_start, legal_indices, train


def _cop_pick(table, enriched: bool):
    """Greedy Cop action-name selector for a trained table (enriched or plain)."""
    def pick(engine: GameEngine) -> str | None:
        legal = legal_indices(engine, Role.COP, table.actions)
        if not legal:
            return None
        return table.actions[table.select(cop_state(engine, enriched), legal, explore=False)]
    return pick


def eval_cop(rules: MatchRules, table, enriched: bool, n: int = 200,
             seed: int = 7, corner: bool = True) -> dict:
    """Roll out ``n`` games (Cop=table vs heuristic Thief); return capture stats."""
    rng = np.random.default_rng(seed)
    cop_pick = _cop_pick(table, enriched)
    wins, barrier_games, moves = 0, 0, []
    for _ in range(n):
        eng = GameEngine(rules)
        if corner:
            cop, thief = _corner_start(eng, rng)
        else:
            cop = rules.cop_start
            thief = rules.thief_start
        eng.reset(cop=cop, thief=thief)
        placed = False
        for _ in range(rules.max_moves + 1):
            if eng.state.is_terminal():
                break
            role = eng.state.turn
            name = cop_pick(eng) if role is Role.COP else heuristic_pick(role, eng)
            if name is None:
                break
            if name == PLACE_BARRIER:
                placed = True
                eng.place_barrier(role)
            else:
                eng.apply_move(role, Direction(name))
        wins += eng.state.outcome.value == "cop_win"
        barrier_games += placed
        moves.append(eng.state.move_count)
    return {"cop_win_rate": wins / n, "avg_moves": float(np.mean(moves)),
            "barrier_use_rate": barrier_games / n}


def ab_compare(rules: MatchRules, qcfg: dict, episodes: int = 4000,
               n_eval: int = 200, seed: int = 0, weight: float = 0.3) -> dict:
    """Train four Cop variants and return their capture/barrier stats (corner starts).

    The four ablations isolate each factor: baseline, PBRS-only, enrichment-only,
    and PBRS+enrichment+curriculum. Honest expectation — PBRS-only matches the
    baseline (policy-invariant: no harm, no induced barriers); enrichment
    fragments the table and hurts; barrier use stays ~0 because walling is
    suboptimal on an open board.
    """
    variants = {
        "baseline": {},
        "shaping_only": {"shaping_weight": weight},
        "enrich_only": {"enrich_cop": True},
        "shaping_enrich": {"shaping_weight": weight, "enrich_cop": True, "corner_fraction": 0.3},
    }
    out: dict = {}
    for name, kw in variants.items():
        cop, _, _ = train(rules, qcfg, episodes, seed, **kw)
        out[name] = eval_cop(rules, cop, enriched=kw.get("enrich_cop", False),
                             n=n_eval, corner=True)
    return out
