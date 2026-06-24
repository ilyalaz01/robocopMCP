"""Movement strategy — heuristic baseline now, Q-policy added in Phase 4.

The heuristic is a greedy Chebyshev-distance policy: the Cop minimises distance
to its target cell, the Thief maximises it (and never stands still — SPEC §3).
It is the baseline the Q-learning curves are compared against, and it backs the
``suggest_move`` MCP tool until a trained Q-table is wired in.
"""

from __future__ import annotations

from ..constants import Direction, Role
from ..domain.board import Board
from ..domain.models import Position


def heuristic_action(
    role: Role,
    own: Position,
    target: Position,
    board: Board,
    barriers: set[Position],
) -> Direction | None:
    """Return the greedy direction for ``role`` toward/away from ``target``.

    Returns ``None`` only if the agent is completely boxed in (no legal move),
    which the engine treats as forfeiting the turn. Tie-breaks are deterministic
    via ``MOVE_DIRECTIONS`` iteration order, keeping self-play reproducible.
    """
    for_thief = role is Role.THIEF
    moves = board.legal_moves(own, barriers, for_thief=for_thief)
    if not moves:
        return None
    if role is Role.COP:
        return min(moves, key=lambda d: board.step(own, d).chebyshev(target))
    return max(moves, key=lambda d: board.step(own, d).chebyshev(target))


def default_target(role: Role, cop_start: Position, thief_start: Position) -> Position:
    """Fallback target when the opponent is unseen and no belief exists yet.

    The Cop heads toward where the Thief began; the Thief flees from where the
    Cop began. This keeps ``suggest_move`` sensible before any sighting/message.
    """
    return thief_start if role is Role.COP else cop_start
