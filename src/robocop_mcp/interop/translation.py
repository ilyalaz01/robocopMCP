"""Bidirectional translation between our engine and the opponent's wire format.

Driven by an :class:`OpponentProfile` (filled by the capability handshake,
defaulting to the opponent team's documented conventions). OUTGOING: phrase our
move/block as the opponent's natural-language declaration. INCOMING: parse the
opponent's message and extract the AUTHORITATIVE direction/action (coordinates
are non-authoritative, kept only for logging), then map to our internal move.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..constants import Direction
from .constants import DIR_TO_WORD, WORD_TO_DIR

_COORD_RE = re.compile(r"[a-z]\d+")


@dataclass
class OpponentProfile:
    """Discovered (or default) opponent conventions that drive translation."""

    dir_to_word: dict = field(default_factory=lambda: dict(DIR_TO_WORD))
    coord_style: str = "chess_like"
    move_template: str = "I move {word}."
    block_phrase: str = "I place a block."
    loss_phrase: str = "I've lost the game."
    timeout_seconds: int = 60
    robber_alias: str = "robber"  # opponent may say "thief"


class Translator:
    """Phrases our actions and parses the opponent's, per an OpponentProfile."""

    def __init__(self, profile: OpponentProfile | None = None) -> None:
        self.profile = profile or OpponentProfile()
        self._word_to_dir = {w.lower(): d for w, d in
                             {v: k for k, v in self.profile.dir_to_word.items()}.items()}
        # Add the opponent's short diagonal synonyms ("up-right" = NE) without
        # overriding any profile word, so terse diagonals don't degrade to cardinals.
        for word, direction in WORD_TO_DIR.items():
            self._word_to_dir.setdefault(word.lower(), direction)
        # Longest phrases first so "up-right diagonal"/"up-right" win over "up"/"right".
        self._phrases = sorted(self._word_to_dir, key=len, reverse=True)

    # --- coordinates (non-authoritative) --------------------------------
    @staticmethod
    def cell_to_coord(x: int, y: int) -> str:
        """Our (x, y) → chess-like coordinate, e.g. (2, 2) → 'c3'."""
        return f"{chr(97 + x)}{y + 1}"

    @staticmethod
    def coord_to_cell(coord: str) -> tuple[int, int]:
        """Chess-like coordinate → our (x, y), e.g. 'c3' → (2, 2)."""
        return ord(coord[0].lower()) - 97, int(coord[1:]) - 1

    # --- outgoing -------------------------------------------------------
    def phrase_move(self, direction: Direction, coord: tuple[int, int] | None = None) -> str:
        """Phrase a move in the opponent's preferred style (+ optional coord)."""
        word = self.profile.dir_to_word[direction]
        msg = self.profile.move_template.format(word=word)
        if coord is not None:
            msg = msg.rstrip(".") + f" to {self.cell_to_coord(*coord)}."
        return msg

    def phrase_block(self) -> str:
        return self.profile.block_phrase

    def phrase_loss(self) -> str:
        return self.profile.loss_phrase

    # --- incoming -------------------------------------------------------
    def parse_action(self, message: str) -> dict:
        """Parse an opponent message → ``{type, direction, coordinate}``.

        ``type`` ∈ move | block | loss | unclear. The declared direction is
        authoritative; a claimed coordinate is captured only for logging.
        """
        text = " ".join(message.lower().split())
        coord_match = _COORD_RE.search(text)
        coordinate = coord_match.group(0) if coord_match else None
        if "place a block" in text or "place block" in text:
            return {"type": "block", "direction": None, "coordinate": coordinate}
        if "lost the game" in text or "i've lost" in text or "i have lost" in text:
            return {"type": "loss", "direction": None, "coordinate": coordinate}
        for phrase in self._phrases:
            if phrase in text:
                return {"type": "move", "direction": self._word_to_dir[phrase],
                        "coordinate": coordinate}
        return {"type": "unclear", "direction": None, "coordinate": coordinate}


def default_profile() -> OpponentProfile:
    """The opponent team's documented conventions (handshake fallback)."""
    return OpponentProfile()


# Re-export for convenience.
__all__ = ["OpponentProfile", "Translator", "default_profile", "WORD_TO_DIR"]
