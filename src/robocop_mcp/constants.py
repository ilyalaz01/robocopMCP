"""Immutable project constants (rubric §6.2 allows Enums + constants here).

Only *fixed* names live here — never tunable values (those come from config).
"""

from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    """The two agents in the pursuit game."""

    COP = "cop"
    THIEF = "thief"


class Outcome(str, Enum):
    """Terminal status of a single sub-game."""

    COP_WIN = "cop_win"
    THIEF_WIN = "thief_win"
    VOID = "void"  # technical loss — re-run (SPEC §3)
    ONGOING = "ongoing"


class Direction(str, Enum):
    """The 8 Moore-neighbourhood moves plus an explicit stay-in-place.

    Stored as ``(dx, dy)`` deltas via :data:`DELTAS`. ``STAY`` is permitted by
    the engine only where rules allow; the Thief may never be hard-coded to use
    it as a strategy (SPEC §3 — thief must always try to evade).
    """

    N = "N"
    NE = "NE"
    E = "E"
    SE = "SE"
    S = "S"
    SW = "SW"
    W = "W"
    NW = "NW"
    STAY = "STAY"


# (dx, dy) with +x = east (right), +y = north (up).
DELTAS: dict[Direction, tuple[int, int]] = {
    Direction.N: (0, 1),
    Direction.NE: (1, 1),
    Direction.E: (1, 0),
    Direction.SE: (1, -1),
    Direction.S: (0, -1),
    Direction.SW: (-1, -1),
    Direction.W: (-1, 0),
    Direction.NW: (-1, 1),
    Direction.STAY: (0, 0),
}

# Movement directions only (excludes STAY) — used by strategy/Q-learning.
MOVE_DIRECTIONS: tuple[Direction, ...] = tuple(d for d in Direction if d is not Direction.STAY)

# Special Cop action name for the Q-table action space (SPEC §9).
PLACE_BARRIER = "PLACE_BARRIER"

GROUP_CODE = "il-nv-ai"
GITHUB_REPO = "https://github.com/ilyalaz01/robocopMCP"
STUDENTS = (
    {"id": "212177943", "name": "Ilya Lazarev"},
    {"id": "316350768", "name": "Nadav Goldin"},
)
