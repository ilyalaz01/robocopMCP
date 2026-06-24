"""Win/capture/scoring rules and action legality (SPEC §3).

Separated from the engine so the *what is legal / who won* policy can be tested
without driving a full state machine, and reused by the MCP servers for the
"mutual position verification" that keeps both sides honest.
"""

from __future__ import annotations

from ..constants import Direction, Outcome, Role
from .board import Board
from .models import GameState, MatchRules, Position


def is_capture(state: GameState) -> bool:
    """Capture = Cop occupies the Thief's exact cell."""
    return state.cop == state.thief


def validate_move(
    board: Board, state: GameState, role: Role, direction: Direction, rules: MatchRules
) -> tuple[bool, str, Position]:
    """Validate a one-step move for ``role`` against authoritative state.

    Returns ``(ok, reason, destination)``. Rejects off-board moves, entering a
    barrier (Thief only), and — for the Thief — a bare ``STAY`` (it must always
    try to evade, SPEC §3). The single-step guarantee is structural: directions
    map to unit deltas, so teleporting is impossible by construction.
    """
    origin = state.cop if role is Role.COP else state.thief
    if direction is Direction.STAY:
        if role is Role.THIEF:
            return False, "thief_must_evade: STAY is not allowed for the Thief", origin
        return True, "stay", origin

    dest = board.step(origin, direction)
    if not board.in_bounds(dest):
        return False, f"off_board: {dest.as_tuple()} outside {board.width}x{board.height}", origin
    if role is Role.THIEF and dest in state.barriers:
        return False, f"barrier_block: {dest.as_tuple()} is impassable", origin
    return True, "ok", dest


def can_place_barrier(state: GameState, rules: MatchRules) -> tuple[bool, str]:
    """Whether the Cop may place a barrier on its current cell right now."""
    if len(state.barriers) >= rules.max_barriers:
        return False, f"barrier_limit: already placed {len(state.barriers)}/{rules.max_barriers}"
    if state.cop in state.barriers:
        return False, "barrier_exists: current cell already a barrier"
    return True, "ok"


def score_subgame(outcome: Outcome, rules: MatchRules) -> tuple[int, int]:
    """Return ``(cop_score, thief_score)`` for a terminal outcome.

    cop_win → Cop ``cop_win`` / Thief ``cop_loss`` (the loser's consolation);
    thief_win → Cop ``thief_loss`` / Thief ``thief_win``. Void games score 0/0.
    """
    if outcome is Outcome.COP_WIN:
        return rules.cop_win, rules.cop_loss
    if outcome is Outcome.THIEF_WIN:
        return rules.thief_loss, rules.thief_win
    return 0, 0


def accumulate(results: list[tuple[int, int]]) -> dict[str, int]:
    """Sum per-sub-game ``(cop, thief)`` scores into series totals."""
    cop = sum(c for c, _ in results)
    thief = sum(t for _, t in results)
    return {"cop": cop, "thief": thief}
