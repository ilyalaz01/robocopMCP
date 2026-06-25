"""Pre-game handshake against the opponent's REAL MCP server (adapted to it).

Their interface (discovered): SSE endpoint, ``auth_token`` param, tools
get_capabilities/propose_ruleset/commit_nonce/reveal_nonce/confirm_role_schedule/
confirm_integrity_promise (no accept_ruleset / exchange_team_identity). We drive
the handshake as the client, print every raw response, derive the sub-game-1 seed
from both nonces, and STOP before sub-game 1.

    uv run python scripts/interop_handshake.py <their_url> <their_token> <their_team> [our_url]
"""

from __future__ import annotations

import asyncio
import json
import sys

from fastmcp import Client

from robocop_mcp.interop.capability_handshake import role_for, team_order
from robocop_mcp.interop.commit_reveal import (
    commitment,
    derive_seed,
    generate_nonce,
    seed_to_positions,
)
from robocop_mcp.interop.constants import INTEGRITY_PROMISE
from robocop_mcp.interop.hashing import RULESET_NAME, ruleset_hash
from robocop_mcp.interop.translation import Translator

OUR_TEAM = "il-nv-ai"


async def _connect(base: str) -> Client:
    for path in ("/sse", "/mcp/", "/mcp", ""):
        url = base.rstrip("/") + path
        try:
            c = Client(url)
            await c.__aenter__()
            await c.list_tools()
            print(f"connected: {url}")
            return c
        except Exception as e:  # noqa: BLE001 - probing
            print(f"  tried {url}: {type(e).__name__}")
    raise SystemExit("could not connect")


def _find(d, *keys):
    """Best-effort pull a value out of an opponent response dict."""
    if isinstance(d, dict):
        for k in keys:
            if k in d and d[k]:
                return d[k]
    return None


async def run(base: str, token: str, their_team: str, our_url: str) -> None:
    c = await _connect(base)

    async def call(step, name, **kw):
        res = await c.call_tool(name, {"auth_token": token, **kw})
        text = " | ".join(getattr(b, "text", "") for b in (res.content or []))
        print(f"{step}) {name}: data={res.data} | content={text[:220]}")
        return res.data, text

    await call("1", "get_capabilities")
    prop, _ = await call("2", "propose_ruleset", ruleset_name=RULESET_NAME,
                         ruleset_hash=ruleset_hash())
    their_hash = _find(prop, "ruleset_hash", "our_ruleset_hash", "hash") or ruleset_hash()
    ruleset_ok = (their_hash == ruleset_hash())

    our_nonce = generate_nonce()
    await call("3", "commit_nonce", sub_game_index=1, nonce_hash=commitment(our_nonce))
    rv, rv_text = await call("4", "reveal_nonce", sub_game_index=1, nonce=our_nonce)
    their_nonce = _find(rv, "nonce", "their_nonce", "our_nonce", "revealed_nonce")

    team_a, team_b = team_order(OUR_TEAM, their_team)
    schedule = {"team_a": team_a, "team_b": team_b,
                "sub_games_1_to_3": {"team_a": "cop", "team_b": "robber"},
                "sub_games_4_to_6": {"team_a": "robber", "team_b": "cop"}}
    await call("5", "confirm_role_schedule", schedule_json=json.dumps(schedule))
    await call("6", "confirm_integrity_promise", message=INTEGRITY_PROMISE)
    await c.__aexit__(None, None, None)

    print("\n===== HANDSHAKE SUMMARY =====")
    print(f"ruleset {RULESET_NAME} / {ruleset_hash()}")
    print(f"ruleset hash agreement: {'OK (their proposed hash matches)' if ruleset_ok else 'CHECK their hash: ' + str(their_hash)}")
    print(f"Team A (cop sg1-3) = {team_a} ; Team B = {team_b}")
    print(f"Our role: sg1-3 = {role_for(1, OUR_TEAM, team_a).value} ; sg4-6 = {role_for(4, OUR_TEAM, team_a).value}")
    if their_nonce:
        nonce_a, nonce_b = (our_nonce, their_nonce) if their_team > OUR_TEAM else (their_nonce, our_nonce)
        seed = derive_seed(nonce_a, nonce_b, 1, ruleset_hash())
        cop, rob = seed_to_positions(seed)
        t = Translator()
        print(f"sub-game 1 seed={seed[:16]}... -> cop={t.cell_to_coord(*cop.as_tuple())} "
              f"robber={t.cell_to_coord(*rob.as_tuple())}")
    else:
        print("their revealed nonce not found in response (seed derivation needs it) — inspect raw above")
    print("STOP before sub-game 1 (as requested).")


if __name__ == "__main__":
    our = sys.argv[4] if len(sys.argv) > 4 else ""
    asyncio.run(run(sys.argv[1], sys.argv[2], sys.argv[3], our))
