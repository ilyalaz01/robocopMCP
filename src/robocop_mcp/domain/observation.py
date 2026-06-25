"""Partial observation — what one agent can actually see (SPEC §3).

Each agent sees only cells within Chebyshev distance ``vision_radius`` of its
own position. The opponent is revealed only when it falls inside that window;
otherwise the agent must infer position from natural-language messages, which
is the whole point of the language layer.
"""

from __future__ import annotations

from ..constants import Role
from .board import Board
from .models import GameState, Observation, Position


def visible_cells(board: Board, center: Position, radius: int) -> list[Position]:
    """All on-board cells within Chebyshev ``radius`` of ``center`` (inclusive)."""
    cells: list[Position] = []
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            cell = center.translate(dx, dy)
            if board.in_bounds(cell):
                cells.append(cell)
    return cells


def build_observation(
    board: Board, state: GameState, role: Role, radius: int, full: bool = False
) -> Observation:
    """Construct the :class:`Observation` for ``role``.

    Partial mode (``full=False``): only cells within Chebyshev ``radius`` are
    seen, and the opponent appears only inside that window (fog of war). Full
    mode (``full=True``, the bonus "open information" profile, ADR-0003): the
    whole board, both positions, and all barriers are always visible.
    """
    self_pos = state.cop if role is Role.COP else state.thief
    opp_pos = state.thief if role is Role.COP else state.cop

    if full:
        window = board.all_cells()
        opponent_visible = True
        barriers = list(state.barriers)
    else:
        window = visible_cells(board, self_pos, radius)
        opponent_visible = self_pos.chebyshev(opp_pos) <= radius
        window_set = {c.as_tuple() for c in window}
        barriers = [b for b in state.barriers if b.as_tuple() in window_set]

    return Observation(
        role=role,
        self_pos=self_pos,
        move_count=state.move_count,
        visible_cells=sorted(c.as_tuple() for c in window),
        visible_barriers=sorted(b.as_tuple() for b in barriers),
        opponent_pos=opp_pos.as_tuple() if opponent_visible else None,
    )
