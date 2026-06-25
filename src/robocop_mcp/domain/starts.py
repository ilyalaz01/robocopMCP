"""Per-sub-game start positions (ADR-0003) — fixes the identical-games defect.

With a deterministic Q-policy, fixed corner starts replay the same game six
times. This module derives **distinct, non-overlapping** start pairs per
sub-game so trajectories differ:

- ``fixed_pairs``: the explicit table from config / ``SHARED_RULES.md`` — two
  independent codebases get byte-identical starts (needed for the bonus match).
- ``seeded_random``: reproducible distinct pairs derived from ``start_seed``.
- ``fixed`` (legacy): the single configured corner pair, repeated.
"""

from __future__ import annotations

import numpy as np

from .models import MatchRules, Position


def _seeded(rules: MatchRules, num_games: int) -> list[tuple[Position, Position]]:
    """Reproducible, distinct, non-overlapping pairs derived from ``start_seed``."""
    rng = np.random.default_rng(rules.start_seed)
    w, h = rules.grid_width, rules.grid_height
    seen: set = set()
    out: list[tuple[Position, Position]] = []
    while len(out) < num_games:
        cop = (int(rng.integers(w)), int(rng.integers(h)))
        thief = (int(rng.integers(w)), int(rng.integers(h)))
        if cop == thief or (cop, thief) in seen:
            continue
        seen.add((cop, thief))
        out.append((Position(*cop), Position(*thief)))
    return out


def generate_starts(rules: MatchRules, num_games: int) -> list[tuple[Position, Position]]:
    """Return ``num_games`` ``(cop_start, thief_start)`` pairs per ``rules.start_mode``."""
    if rules.start_mode == "fixed_pairs" and rules.start_pairs:
        pairs = list(rules.start_pairs)
        return [pairs[i % len(pairs)] for i in range(num_games)]
    if rules.start_mode == "seeded_random":
        return _seeded(rules, num_games)
    return [(rules.cop_start, rules.thief_start) for _ in range(num_games)]
