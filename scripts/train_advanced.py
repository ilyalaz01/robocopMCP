"""Train + save the advanced-profile Q-tables and the barrier A/B study (ADR-0004).

Trains the Cop/Thief with PBRS + enriched state + corner curriculum, saves them to
``results/qtables_advanced`` (separate from the solo/bonus ``results/qtables`` — so
those are untouched), and writes the four-variant A/B comparison to JSON. Run with
``uv run python scripts/train_advanced.py``.
"""

from __future__ import annotations

import json

import numpy as np

from robocop_mcp.constants import PLACE_BARRIER
from robocop_mcp.domain.models import MatchRules
from robocop_mcp.learning.ab_barriers import ab_compare
from robocop_mcp.learning.trainer import train
from robocop_mcp.shared.config import ConfigManager


def main() -> None:
    cfg = ConfigManager(profile="advanced")
    ql = cfg.game()["q_learning"]
    rules = MatchRules.from_config(cfg.game())
    out = cfg.root / "results" / ql["qtable_dir"]
    weight = cfg.game()["reward_shaping"]["weight"]

    cop_q, _, _ = train(rules, ql, ql["episodes"], seed=0, out_dir=out,
                        shaping_weight=weight, enrich_cop=True,
                        corner_fraction=ql["corner_fraction"])
    bi = cop_q.actions.index(PLACE_BARRIER)
    barrier_argmax = sum(1 for row in cop_q.q.values() if int(np.argmax(row)) == bi)

    ab = ab_compare(rules, ql, episodes=4000, n_eval=200, seed=0, weight=weight)
    (out / "ab_barriers.json").write_text(json.dumps(ab, indent=2))
    print(f"saved advanced tables to {out} (cop states={len(cop_q.q)}, "
          f"barrier-argmax states={barrier_argmax})")
    print(json.dumps(ab, indent=2))


if __name__ == "__main__":
    main()
