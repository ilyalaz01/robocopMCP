"""Commit-reveal seed + deterministic placement — BIT-EXACT to Team B (ADR-0005).

Confirmed spec (mismatch → series = 0):

  payload  = bytes.fromhex(nonce_A) + bytes.fromhex(nonce_B)
             + sub_game_index.to_bytes(4, "big")
             + ruleset_hash.lower().encode("utf-8")          # the 64-char hex STRING
  seed_i   = sha256(payload).hexdigest()                     # 64-char lowercase hex

  rng    = random.Random(bytes.fromhex(seed_i))              # local Mersenne Twister
  cells  = rank-major a1,b1,c1,d1,e1,a2,...,e5  (files change faster)
  cop    = rng.choice(cells)
  robber = rng.choice([c for c in cells if c != cop])        # cop first, robber second

Nonces are hex-DECODED to raw bytes before concatenation (not strings); the
sub-game index is 4 bytes big-endian; ruleset_hash is the hex STRING in UTF-8.
"""

from __future__ import annotations

import hashlib
import random
import secrets

from ..domain.models import Position


def generate_nonce() -> str:
    """A fresh random secret nonce as hex (hex-decodable for the seed payload)."""
    return secrets.token_hex(16)


def commitment(nonce: str) -> str:
    """Public commitment = raw hex SHA-256 of the nonce (sent before reveal)."""
    return hashlib.sha256(nonce.encode("utf-8")).hexdigest()


def verify(nonce: str, claimed_commitment: str) -> bool:
    """Check a revealed nonce against its earlier commitment."""
    return commitment(nonce) == claimed_commitment


def derive_seed(nonce_a: str, nonce_b: str, sub_game_index: int, ruleset_hash: str) -> str:
    """Bit-exact sub-game seed (64-char lowercase hex). ``nonce_a`` = Team A's."""
    payload = (bytes.fromhex(nonce_a) + bytes.fromhex(nonce_b)
               + sub_game_index.to_bytes(4, "big")
               + ruleset_hash.lower().encode("utf-8"))
    return hashlib.sha256(payload).hexdigest()


def _cells(width: int, height: int) -> list[Position]:
    """Rank-major cell list a1,b1,...,e5 (file changes faster) — index order matters."""
    return [Position(x, y) for y in range(height) for x in range(width)]


def seed_to_positions(seed_hex: str, width: int = 5, height: int = 5) -> tuple[Position, Position]:
    """Deterministic (Cop, Robber) start cells via ``random.Random(bytes(seed))``."""
    rng = random.Random(bytes.fromhex(seed_hex))
    cells = _cells(width, height)
    cop = rng.choice(cells)
    robber = rng.choice([c for c in cells if c != cop])
    return cop, robber
