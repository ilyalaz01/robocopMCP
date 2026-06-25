"""Commit-reveal random start positions (their §5.7 / §7) — BIT-EXACT (ADR-0005).

Both teams MUST derive identical seeds and cells or starts disagree. Documented
DEFAULTS (flagged in ``_build/INTEROP_STATUS.md`` for opponent confirmation):
- commitment = ``sha256:<hex(nonce_utf8)>``;
- ``seed_i = SHA256(nonce_A || nonce_B || str(i) || ruleset_hash)`` — the variant
  WITH ruleset_hash (their game-rules §4.5 + assignment §7.3; assignment §5.7 omits
  it — FLAGGED);
- seed→cell: language-agnostic walk of the seed hex over cells in coordinate order
  ``a1,b1,...,a2,...`` (index → ``(k % w, k // w)``), Robber resampled until disjoint.
"""

from __future__ import annotations

import secrets

from ..domain.models import Position
from .hashing import sha256_hex


def generate_nonce() -> str:
    """A fresh random secret nonce (hex)."""
    return secrets.token_hex(16)


def commitment(nonce: str) -> str:
    """The public commitment ``sha256:<hash of nonce>`` sent before reveal."""
    return "sha256:" + sha256_hex(nonce)


def verify(nonce: str, claimed_commitment: str) -> bool:
    """Check a revealed nonce against its earlier commitment."""
    return commitment(nonce) == claimed_commitment


def derive_seed(nonce_a: str, nonce_b: str, sub_game_index: int, ruleset_hash: str) -> str:
    """``seed_i = SHA256(nonce_A || nonce_B || str(i) || ruleset_hash)`` (hex)."""
    return sha256_hex(f"{nonce_a}{nonce_b}{sub_game_index}{ruleset_hash}")


def _idx_to_cell(idx: int, width: int) -> Position:
    """Cell index in coordinate order a1,b1,... → Position (x = file, y = rank)."""
    return Position(idx % width, idx // width)


def seed_to_positions(seed_hex: str, width: int = 5, height: int = 5) -> tuple[Position, Position]:
    """Deterministically derive disjoint (Cop, Robber) start cells from a seed."""
    n = width * height
    digits = seed_hex
    cop_idx = int(digits[0:8], 16) % n
    cursor = 8
    rob_idx = int(digits[cursor:cursor + 8], 16) % n
    while rob_idx == cop_idx:  # resample until disjoint (their §7.4 step 8)
        cursor += 8
        if cursor + 8 > len(digits):
            digits += sha256_hex(digits)  # extend deterministically if exhausted
        rob_idx = int(digits[cursor:cursor + 8], 16) % n
    return _idx_to_cell(cop_idx, width), _idx_to_cell(rob_idx, width)
