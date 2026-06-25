"""GameEngine — the authoritative sub-game state machine (SPEC §3).

Drives one pursuit round: Thief-first turn order, one-step moves, Cop barrier
placement, capture/timeout resolution, and scoring. It composes :mod:`board`,
:mod:`rules`, and :mod:`observation`; it performs no I/O and holds no network or
LLM concerns, so it is fully deterministic and unit-testable.
"""

from __future__ import annotations

from ..constants import Direction, Outcome, Role
from .board import Board
from .models import GameState, MatchRules, MoveResult, Observation, Position, SubGameResult
from .observation import build_observation
from .rules import can_place_barrier, is_capture, score_subgame, validate_move


class GameEngine:
    """Owns the state of a single sub-game and applies validated actions."""

    def __init__(self, rules: MatchRules) -> None:
        self.rules = rules
        self.board = Board(rules.grid_width, rules.grid_height)
        self.state = self._fresh_state()

    def _fresh_state(self) -> GameState:
        """Initial state: agents at their start cells, Thief to move."""
        return GameState(cop=self.rules.cop_start, thief=self.rules.thief_start, turn=Role.THIEF)

    def reset(self, cop: Position | None = None, thief: Position | None = None) -> None:
        """Start a new sub-game, optionally overriding start cells (negotiation)."""
        self.state = self._fresh_state()
        if cop is not None:
            self.state.cop = cop
        if thief is not None:
            self.state.thief = thief

    def observe(self, role: Role) -> Observation:
        """Observation for ``role`` — partial (vision_radius) or full per the profile."""
        full = self.rules.visibility == "full"
        return build_observation(self.board, self.state, role, self.rules.vision_radius, full)

    def _digest(self) -> dict:
        """Compact authoritative snapshot for logging / mutual verification."""
        return {
            "cop": self.state.cop.as_tuple(),
            "thief": self.state.thief.as_tuple(),
            "turn": self.state.turn.value,
            "move_count": self.state.move_count,
            "barriers": sorted(b.as_tuple() for b in self.state.barriers),
            "outcome": self.state.outcome.value,
        }

    def _guard(self, role: Role) -> str | None:
        """Return a rejection reason if ``role`` may not act now, else ``None``."""
        if self.state.is_terminal():
            return f"game_over: outcome already {self.state.outcome.value}"
        if self.state.turn is not role:
            return f"not_your_turn: it is {self.state.turn.value}'s turn"
        return None

    def _advance(self) -> None:
        """Increment the ply count, resolve capture/timeout, and pass the turn."""
        self.state.move_count += 1
        if is_capture(self.state):
            self.state.outcome = Outcome.COP_WIN
        elif self.state.move_count >= self.rules.max_moves:
            # Thief survived the full move budget → evasion win (SPEC §3).
            self.state.outcome = Outcome.THIEF_WIN
        self.state.turn = Role.COP if self.state.turn is Role.THIEF else Role.THIEF

    def apply_move(self, role: Role, direction: Direction) -> MoveResult:
        """Validate and apply a one-step move; advance the state machine."""
        reason = self._guard(role)
        if reason:
            return MoveResult(False, reason, None, False, self._digest())

        ok, why, dest = validate_move(self.board, self.state, role, direction, self.rules)
        if not ok:
            return MoveResult(False, why, direction, False, self._digest())

        if role is Role.COP:
            self.state.cop = dest
        else:
            self.state.thief = dest
        self.state.history.append({"role": role.value, "dir": direction.value, "to": dest.as_tuple()})
        self._advance()
        return MoveResult(True, why, direction, False, self._digest())

    def place_barrier(self, role: Role) -> MoveResult:
        """Cop-only: forfeit the move and mark the current cell impassable."""
        reason = self._guard(role)
        if reason:
            return MoveResult(False, reason, None, False, self._digest())
        if role is not Role.COP:
            return MoveResult(False, "barrier_forbidden: only the Cop places barriers",
                              None, False, self._digest())
        ok, why = can_place_barrier(self.state, self.rules)
        if not ok:
            return MoveResult(False, why, None, False, self._digest())

        self.state.barriers.add(self.state.cop)
        self.state.history.append({"role": role.value, "barrier": self.state.cop.as_tuple()})
        self._advance()  # placing forfeits the move but still consumes the turn/ply
        return MoveResult(True, "barrier_placed", None, True, self._digest())

    def result(self, index: int) -> SubGameResult:
        """Build the :class:`SubGameResult` for the finished sub-game."""
        cop_score, thief_score = score_subgame(self.state.outcome, self.rules)
        return SubGameResult(
            index=index, outcome=self.state.outcome, moves=self.state.move_count,
            cop_score=cop_score, thief_score=thief_score,
            void=self.state.outcome is Outcome.VOID,
        )
