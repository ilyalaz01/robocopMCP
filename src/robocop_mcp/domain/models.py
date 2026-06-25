"""Domain dataclasses — the typed vocabulary of the pursuit game.

Pure data only (no rules, no I/O), so every other domain module depends on
these shapes rather than on each other. Rules live in :mod:`rules`, geometry in
:mod:`board`, the state machine in :mod:`engine`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..constants import Direction, Outcome, Role


@dataclass(frozen=True)
class Position:
    """An immutable grid cell ``(x, y)`` with +x east, +y north."""

    x: int
    y: int

    def translate(self, dx: int, dy: int) -> Position:
        """Return a new position shifted by ``(dx, dy)`` (no bounds check)."""
        return Position(self.x + dx, self.y + dy)

    def chebyshev(self, other: Position) -> int:
        """Chebyshev (Moore/king-move) distance — the game's vision metric."""
        return max(abs(self.x - other.x), abs(self.y - other.y))

    def as_tuple(self) -> tuple[int, int]:
        """Plain tuple form for JSON logging and Q-state encoding."""
        return (self.x, self.y)


@dataclass(frozen=True)
class MatchRules:
    """Effective ruleset for a series — the negotiated/config-derived parameters."""

    grid_width: int
    grid_height: int
    max_moves: int
    max_barriers: int
    vision_radius: int
    num_games: int
    num_cops: int
    cop_win: int
    thief_win: int
    cop_loss: int
    thief_loss: int
    cop_start: Position
    thief_start: Position
    # Profile-driven (ADR-0003): observation + messaging mode and start scheme.
    visibility: str = "partial"  # "partial" | "full"
    deception: bool = True
    start_mode: str = "fixed"  # "fixed" | "seeded_random" | "fixed_pairs"
    start_seed: int = 0
    start_pairs: tuple[tuple[Position, Position], ...] = ()

    @classmethod
    def from_config(cls, game_cfg: dict) -> MatchRules:
        """Build rules from the validated game-config dict (config is the source)."""
        w, h = game_cfg["grid_size"]
        sc = game_cfg["scoring"]
        pairs = tuple(
            (Position(*c), Position(*t)) for c, t in game_cfg.get("start_pairs", [])
        )
        return cls(
            grid_width=w, grid_height=h,
            max_moves=game_cfg["max_moves"], max_barriers=game_cfg["max_barriers"],
            vision_radius=game_cfg["vision_radius"], num_games=game_cfg["num_games"],
            num_cops=game_cfg.get("negotiation", {}).get("num_cops", 1),
            cop_win=sc["cop_win"], thief_win=sc["thief_win"],
            cop_loss=sc["cop_loss"], thief_loss=sc["thief_loss"],
            cop_start=Position(0, 0), thief_start=Position(w - 1, h - 1),
            visibility=game_cfg.get("visibility", "partial"),
            deception=game_cfg.get("deception", True),
            start_mode=game_cfg.get("start_mode", "fixed"),
            start_seed=game_cfg.get("start_seed", 0),
            start_pairs=pairs,
        )

    def with_overrides(self, **changes) -> MatchRules:
        """Return a copy with negotiated overrides (e.g. ``max_barriers=7``)."""
        from dataclasses import replace

        return replace(self, **changes)


@dataclass
class GameState:
    """Mutable authoritative state of a single sub-game."""

    cop: Position
    thief: Position
    turn: Role = Role.THIEF  # Thief moves first (SPEC §3)
    move_count: int = 0
    barriers: set[Position] = field(default_factory=set)
    outcome: Outcome = Outcome.ONGOING
    history: list[dict] = field(default_factory=list)

    def is_terminal(self) -> bool:
        """True once the sub-game has resolved (capture, timeout, or void)."""
        return self.outcome is not Outcome.ONGOING


@dataclass
class Observation:
    """Partial view for one agent — only cells within ``vision_radius``."""

    role: Role
    self_pos: Position
    move_count: int
    visible_cells: list[tuple[int, int]]
    visible_barriers: list[tuple[int, int]]
    opponent_pos: tuple[int, int] | None  # None when outside the vision window


@dataclass
class MoveResult:
    """Outcome of applying one action against the authoritative state."""

    ok: bool
    reason: str
    direction: Direction | None
    placed_barrier: bool
    state_digest: dict


@dataclass
class SubGameResult:
    """Result of one completed (or void) sub-game."""

    index: int
    outcome: Outcome
    moves: int
    cop_score: int
    thief_score: int
    void: bool = False
