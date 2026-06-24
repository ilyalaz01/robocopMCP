"""One-at-a-time (OAT) parameter sensitivity + Q-vs-heuristic comparison.

Drives the notebook's sensitivity heatmaps/line charts (rubric §8.1): vary one
parameter at a time, retrain a Q-cop, and measure cop win-rate + capture time
against a heuristic thief. Separated from :mod:`experiments` to keep both files
small and single-purpose.
"""

from __future__ import annotations

from ..domain.models import MatchRules
from .experiments import eval_stats, heuristic_pick, q_pick
from .trainer import train


def q_vs_heuristic(rules: MatchRules, qcfg: dict, episodes: int = 400,
                   n_eval: int = 60, seed: int = 0) -> dict:
    """Compare a trained Q-cop to the heuristic-cop baseline (vs heuristic thief)."""
    cop_q, _, history = train(rules, qcfg, episodes, seed)
    q_stats = eval_stats(rules, lambda r, e: q_pick(cop_q, r, e), heuristic_pick, n_eval, seed + 1)
    base = eval_stats(rules, heuristic_pick, heuristic_pick, n_eval, seed + 1)
    return {"q": q_stats, "heuristic": base, "history": history}


def _rules_for(param: str, value, base_game: dict) -> tuple[MatchRules, dict]:
    """Build (rules, qcfg-overrides) for a single OAT parameter value."""
    game = dict(base_game)
    qover: dict = {}
    if param in ("epsilon", "gamma"):
        qover[param] = value
    elif param == "grid_size":
        game["grid_size"] = [value, value]
    elif param == "max_barriers":
        return MatchRules.from_config(game).with_overrides(max_barriers=value), qover
    return MatchRules.from_config(game), qover


def sensitivity_oat(param: str, values, base_game: dict, qcfg: dict,
                    episodes: int = 300, n_eval: int = 40) -> dict:
    """Return ``{value: {cop_win_rate, avg_moves}}`` varying ``param`` alone."""
    results: dict = {}
    for value in values:
        rules, qover = _rules_for(param, value, base_game)
        merged = {**qcfg, **qover}
        cop_q, _, _ = train(rules, merged, episodes, seed=0)
        results[value] = eval_stats(
            rules, lambda r, e, cq=cop_q: q_pick(cq, r, e), heuristic_pick, n_eval, seed=7
        )
    return results
