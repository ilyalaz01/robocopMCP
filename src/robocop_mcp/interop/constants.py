"""Interop constants — the opponent team's documented conventions (defaults).

These map our internal vocabulary to the opponent's exact wording from
``_build/opponent/`` (assignment.md + cop_rob_game_rules.md). They are the
*defaults* the capability handshake starts from and adapts away from for any
other team. Nothing here changes the solo/bonus systems.
"""

from __future__ import annotations

from ..constants import Direction

# Our Direction → opponent canonical direction word (their §5.4 / §9.2).
DIR_TO_WORD: dict[Direction, str] = {
    Direction.N: "up",
    Direction.NE: "up-right diagonal",
    Direction.E: "right",
    Direction.SE: "right-down diagonal",
    Direction.S: "down",
    Direction.SW: "down-left diagonal",
    Direction.W: "left",
    Direction.NW: "left-up diagonal",
}
WORD_TO_DIR: dict[str, Direction] = {word: d for d, word in DIR_TO_WORD.items()}

PLACE_BLOCK_PHRASE = "I place a block."
LOSS_ADMISSION_PHRASE = "I've lost the game."

# Terminal reason codes (their §25). Winner side annotated for scoring.
TERMINAL_CODES = {
    "cop_capture": "cop", "robber_moved_into_cop": "cop", "robber_no_legal_move": "cop",
    "cop_no_legal_action": "robber", "robber_illegal_action": "cop",
    "cop_illegal_action": "robber", "robber_invalid_action_retry_failed": "cop",
    "cop_invalid_action_retry_failed": "robber", "robber_timeout_retry_failed": "cop",
    "cop_timeout_retry_failed": "robber", "round_limit_reached": "robber",
    "technical_failure_rerun": None, "protocol_failure": None,
}


def outcome_for(code: str | None) -> str | None:
    """Winner side ('cop'/'robber') for a terminal-reason code, else None (their §25)."""
    return TERMINAL_CODES.get(code) if code else None


# Canonical pre-game texts (assignment.md §5.3 / §5.9). Bit-exact items — see ADR-0005.
RULESET_NAME = "cop-robber-grid-v1"
ACCEPT_TEMPLATE = "I accept ruleset {name} with hash {hash}."
INTEGRITY_PROMISE = (
    "I agree to follow the accepted ruleset.\n"
    "I will not cheat, lie, or intentionally misrepresent actions, positions, blocks, "
    "logs, legal moves, terminal conditions, scores, or reports.\n"
    "I will maintain my own inferred board state from the initial positions and public "
    "action history.\n"
    "I will admit loss if I have no legal action."
)
