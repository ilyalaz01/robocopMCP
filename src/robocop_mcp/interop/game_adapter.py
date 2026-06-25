"""InteropGame — the opponent's ruleset on top of our existing GameEngine.

Reuses :class:`GameEngine` for state, movement, capture, scoring and terminal
state, and adds the two interop-specific differences (ADR-0005): blocks are
impassable to BOTH players (ours block only the Thief) and a sub-game is 25 full
rounds = 50 plies. Robber == our Thief, Cop == our Cop. Emits the opponent's
exact terminal-reason codes.
"""

from __future__ import annotations

from ..constants import Direction, Outcome, Role
from ..domain.engine import GameEngine
from ..domain.models import MatchRules, Position
from ..domain.rules import can_place_barrier

ROLE_FROM_STR = {"cop": Role.COP, "robber": Role.THIEF, "thief": Role.THIEF}
STR_FROM_ROLE = {Role.COP: "cop", Role.THIEF: "robber"}


def build_rules(grid_w: int, grid_h: int, max_rounds: int, max_barriers: int) -> MatchRules:
    """MatchRules for an interop sub-game (max_moves = 2×rounds = both plies)."""
    return MatchRules.from_config({
        "grid_size": [grid_w, grid_h], "max_moves": 2 * max_rounds,
        "max_barriers": max_barriers, "vision_radius": 1, "num_games": 6,
        "scoring": {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5},
    })


class InteropGame:
    """One interop sub-game over our engine; barriers block both players."""

    def __init__(self, rules: MatchRules) -> None:
        self.engine = GameEngine(rules)
        self.terminal_code: str | None = None

    def start(self, cop: Position, robber: Position) -> None:
        """Reset to the agreed initial Cop/Robber cells (Robber moves first)."""
        self.engine.reset(cop=cop, thief=robber)
        self.terminal_code = None

    def _own(self, role: Role) -> Position:
        return self.engine.state.cop if role is Role.COP else self.engine.state.thief

    def legal_move_dirs(self, role: Role) -> list[Direction]:
        """Legal move directions — barriers block BOTH players (for_thief=True)."""
        return self.engine.board.legal_moves(self._own(role), self.engine.state.barriers,
                                             for_thief=True)

    def can_block(self, role: Role) -> bool:
        """Whether the Cop may place a block right now (own cell, under budget)."""
        return role is Role.COP and can_place_barrier(self.engine.state, self.engine.rules)[0]

    def has_legal_action(self, role: Role) -> bool:
        """True if ``role`` has any legal action this turn (else it loses)."""
        return bool(self.legal_move_dirs(role)) or self.can_block(role)

    def _resolve(self, role: Role) -> str | None:
        """Map the engine outcome after an action to an interop terminal code."""
        outcome = self.engine.state.outcome
        if outcome is Outcome.COP_WIN:
            return "cop_capture" if role is Role.COP else "robber_moved_into_cop"
        if outcome is Outcome.THIEF_WIN:
            return "round_limit_reached"
        return None

    def apply_move(self, role: Role, direction: Direction) -> str | None:
        """Apply a move; return a terminal code (loss/win/none). Sets terminal_code."""
        dest = self.engine.board.step(self._own(role), direction)
        legal = self.engine.board.is_passable(dest, self.engine.state.barriers, for_thief=True)
        if not legal:
            self.terminal_code = f"{STR_FROM_ROLE[role]}_illegal_action"
            return self.terminal_code
        self.engine.apply_move(role, direction)
        self.terminal_code = self._resolve(role)
        return self.terminal_code

    def apply_block(self, role: Role) -> str | None:
        """Cop places a block on its cell; illegal placement → cop loss."""
        if not self.can_block(role):
            self.terminal_code = "cop_illegal_action"
            return self.terminal_code
        self.engine.place_barrier(role)
        self.terminal_code = self._resolve(role)
        return self.terminal_code

    def admit_loss(self, role: Role) -> str:
        """Record a forced-loss admission for ``role`` (no legal action)."""
        self.terminal_code = ("robber_no_legal_move" if role is Role.THIEF
                              else "cop_no_legal_action")
        return self.terminal_code

    def no_legal_action_code(self, role: Role) -> str:
        """Terminal code when ``role`` has no legal action at the start of its turn."""
        return self.admit_loss(role)
