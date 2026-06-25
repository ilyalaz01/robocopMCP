"""Canonical JSON + SHA-256 — BIT-EXACT to Team B's confirmed spec (ADR-0005).

Aligned to the opponent's confirmed conventions (mismatch → series = 0):
- canonical JSON = ``json.dumps(obj, sort_keys=True, separators=(",", ":"))`` with
  the DEFAULT ``ensure_ascii=True``, UTF-8 encoded;
- all hashes are **raw lowercase hex, 64 chars, NO ``sha256:`` prefix**;
- ``ruleset_hash`` = SHA-256 of the rules file ``cop_rob_game_rules.md`` as-is
  (confirmed value below); the file in ``_build/opponent/`` hashes to it byte-for-byte.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

# Confirmed wire ruleset hash (raw hex, no prefix) = SHA-256 of cop_rob_game_rules.md.
RULESET_HASH = "a0df8e78a545501805496d36110fa6e2850d073d72639632a3abac354fc35140"
RULESET_NAME = "cop-robber-grid-v1"


def canonical_json(obj: Any) -> str:
    """Deterministic JSON (sorted keys, compact separators, default ensure_ascii)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sha256_hex(data: str | bytes) -> str:
    """Lowercase 64-char hex SHA-256 of a string (UTF-8) or bytes."""
    raw = data.encode("utf-8") if isinstance(data, str) else data
    return hashlib.sha256(raw).hexdigest()


def hash_payload(obj: Any) -> str:
    """Raw hex SHA-256 of the canonical JSON of ``obj`` (results/reports)."""
    return sha256_hex(canonical_json(obj).encode("utf-8"))


# Back-compat alias matching Team B's function name.
compute_report_hash = hash_payload


def file_ruleset_hash(path: Path) -> str:
    """SHA-256 of a rules file as-is (the documented source of ``ruleset_hash``)."""
    return sha256_hex(Path(path).read_bytes())


def ruleset_hash(ruleset: Any = None) -> str:
    """The agreed wire ruleset hash (raw hex, no prefix)."""
    return RULESET_HASH
