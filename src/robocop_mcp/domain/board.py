"""Board geometry — bounds, neighbours, and barrier passability.

Pure spatial logic with no notion of *whose* turn it is or *who wins*; that is
the rules/engine's job. Keeping geometry isolated makes movement trivially
testable and reusable by the observation and strategy layers.
"""

from __future__ import annotations

from ..constants import DELTAS, MOVE_DIRECTIONS, Direction
from .models import Position


class Board:
    """A `width × height` grid with impassable barrier cells.

    Setup:  width, height (ints > 0).
    Input:  positions + directions.
    Output: bounds checks, neighbour lists, translated positions.
    """

    def __init__(self, width: int, height: int) -> None:
        if width <= 0 or height <= 0:
            raise ValueError(f"Grid dimensions must be positive, got {width}x{height}")
        self.width = width
        self.height = height

    def in_bounds(self, pos: Position) -> bool:
        """True if ``pos`` lies on the board."""
        return 0 <= pos.x < self.width and 0 <= pos.y < self.height

    def step(self, pos: Position, direction: Direction) -> Position:
        """Translate ``pos`` one cell in ``direction`` (may leave the board)."""
        dx, dy = DELTAS[direction]
        return pos.translate(dx, dy)

    def is_passable(self, pos: Position, barriers: set[Position], *, for_thief: bool) -> bool:
        """Whether ``pos`` may be entered.

        Barriers block only the Thief (SPEC §3); the Cop never needs to enter a
        barrier cell because placing one forfeits its move and it stays put.
        """
        if not self.in_bounds(pos):
            return False
        return not (for_thief and pos in barriers)

    def legal_moves(
        self, pos: Position, barriers: set[Position], *, for_thief: bool
    ) -> list[Direction]:
        """All 8 directions whose destination is on-board and passable.

        ``STAY`` is intentionally excluded — callers add it only where rules
        allow, and the Thief must never rely on it (it must try to evade).
        """
        out: list[Direction] = []
        for direction in MOVE_DIRECTIONS:
            dest = self.step(pos, direction)
            if self.is_passable(dest, barriers, for_thief=for_thief):
                out.append(direction)
        return out

    def all_cells(self) -> list[Position]:
        """Every cell on the board (used for rendering and exhaustive checks)."""
        return [Position(x, y) for x in range(self.width) for y in range(self.height)]
