"""Final bit-exact agreement step: exchange sub-game results + report hashes.

Pushes our authoritative per-sub-game results to the opponent
(``confirm_sub_game_result``) and pulls their final report hash
(``confirm_final_report`` / ``get_final_report``) so :func:`finalize` can compare
it canonically against ours and set ``mutual_agreement``.

Graceful by design: if the opponent's server exposes no hash-returning tool (Team
B's current server records results without validating and has no such tool),
:func:`fetch_opponent_report_hash` returns ``None`` and agreement is reported as
unavailable rather than faked.
"""

from __future__ import annotations

import contextlib

from .finalize import comparable_hash

_RESULT_KEYS = ("sub_game_index", "terminal_reason", "winner_role", "scores")
_HASH_FIELDS = ("report_hash", "hash", "our_hash", "final_hash", "their_hash")


async def push_our_results(their, report: dict) -> list[dict]:
    """Send each of our sub-game results to the opponent's confirm_sub_game_result."""
    acks: list[dict] = []
    for s in report["sub_games"]:
        body = {k: s[k] for k in _RESULT_KEYS}
        acks.append(await their.confirm_sub_game_result(
            s["sub_game_index"], s["log_hash"], body))
    return acks


async def fetch_opponent_report_hash(their, our_hash: str) -> str | None:
    """Pull the opponent's 64-hex report hash, or None if no such tool exists."""
    for getter in (lambda: their.confirm_final_report(our_hash),
                   lambda: their.get_final_report()):
        resp = None
        with contextlib.suppress(Exception):
            resp = await getter()
        if not isinstance(resp, dict):
            continue
        if "report" in resp and isinstance(resp["report"], dict):  # hash it ourselves
            return comparable_hash(resp["report"])
        for f in _HASH_FIELDS:
            v = resp.get(f)
            if isinstance(v, str) and len(v) == 64:
                return v
    return None
