"""Potential-based reward shaping + enriched Cop state (ADR-0004).

`Phi(s) = -(legal escape moves the Thief has)` makes states where the Thief is
boxed in higher-potential. The Cop's shaped reward adds `F = gamma*Phi(s') -
Phi(s)`; a barrier that cuts the Thief's escapes raises Phi, so the Cop learns to
place barriers WHEN they trap — without a flat per-barrier bonus (which would
reward-hack into spam). PBRS is policy-invariant (Ng, Harada & Russell, 1999).
"""

from __future__ import annotations

from ..domain.engine import GameEngine
from .q_learning import encode_state


def thief_escape_count(engine: GameEngine) -> int:
    """Number of legal one-step moves the Thief currently has (its reachable set)."""
    return len(engine.board.legal_moves(
        engine.state.thief, engine.state.barriers, for_thief=True))


def potential(engine: GameEngine) -> float:
    """Phi(s) = -(thief escape count). Higher when the Thief is more boxed in."""
    return -float(thief_escape_count(engine))


def escape_bucket(count: int) -> int:
    """Bucket the Thief's escape count into 0 (0–2), 1 (3–5), 2 (6–8)."""
    if count <= 2:
        return 0
    if count <= 5:
        return 1
    return 2


def cop_state(engine: GameEngine, enriched: bool) -> tuple[int, ...]:
    """Encode the Cop's Q-state, optionally enriched with the escape bucket.

    Enriched (advanced profile) appends the Thief's bucketed escape count so the
    Cop can condition on "nearly cornered". Otherwise it is the plain 2-tuple
    used by solo/bonus, keeping those tables/results unchanged.
    """
    extra = escape_bucket(thief_escape_count(engine)) if enriched else None
    return encode_state(engine.state.cop, engine.state.thief, extra)
