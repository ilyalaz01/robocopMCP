"""Canonical JSON + SHA-256 helpers for bit-exact agreement (ADR-0005).

BIT-EXACT — both teams MUST use the identical canonicalization + hash or the
series voids (hash mismatch → 0). Our documented DEFAULT (flagged in
``_build/INTEROP_STATUS.md`` for opponent confirmation): UTF-8 JSON with
``sort_keys=True`` and compact separators ``(",", ":")``, hashed with SHA-256,
prefixed ``sha256:``.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

# The fixed official ruleset object (their §5.4) — the source for ruleset_hash.
OFFICIAL_RULESET: dict[str, Any] = {
    "ruleset_name": "cop-robber-grid-v1",
    "grid_size": [5, 5],
    "wrap_around": False,
    "diagonal_movement": True,
    "diagonal_corner_cutting": True,
    "passing": False,
    "robber_moves_first": True,
    "max_rounds": 25,
    "num_valid_sub_games": 6,
    "cop_block_budget": 5,
    "scoring": {"cop_win": {"cop": 20, "robber": 5},
                "robber_win": {"cop": 5, "robber": 10}},
    "invalid_or_unclear_action_retries": 1,
    "timeout_retries": 1,
    "illegal_action_causes_immediate_loss": True,
}


def canonical_json(obj: Any) -> str:
    """Deterministic JSON string (sorted keys, compact separators, UTF-8)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(data: str | bytes) -> str:
    """Lowercase hex SHA-256 of a string (UTF-8) or bytes."""
    raw = data.encode("utf-8") if isinstance(data, str) else data
    return hashlib.sha256(raw).hexdigest()


def hash_payload(obj: Any) -> str:
    """``sha256:<hex>`` of the canonical JSON of ``obj`` (results/reports)."""
    return "sha256:" + sha256_hex(canonical_json(obj))


def ruleset_hash(ruleset: dict | None = None) -> str:
    """Hash of the official ruleset object → the agreed ``ruleset_hash``."""
    return hash_payload(ruleset or OFFICIAL_RULESET)
