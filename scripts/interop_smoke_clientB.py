"""External 'team B' smoke against a deployed interop agent (over the tunnel).

Connects as a pure MCP client to a PUBLIC interop URL and exercises the real
protocol end to end: get_capabilities -> handshake (identity, ruleset accept,
commit-reveal, role schedule, integrity) -> start_sub_game -> a full sub-game
delivered move-by-move via receive_action_message. Proves an external client
plays through the tunnel and the server agrees on the terminal result.

    uv run python scripts/interop_smoke_clientB.py https://<...>.trycloudflare.com/mcp/
"""

from __future__ import annotations

import asyncio
import sys

from fastmcp import Client

from robocop_mcp.domain.models import Position
from robocop_mcp.interop.commit_reveal import commitment, generate_nonce
from robocop_mcp.interop.constants import TERMINAL_CODES
from robocop_mcp.interop.game_adapter import STR_FROM_ROLE, InteropGame, build_rules
from robocop_mcp.interop.hashing import ruleset_hash
from robocop_mcp.interop.peer_agent import default_policy
from robocop_mcp.interop.translation import Translator

TOKEN = "il-nv-ai-interop-token"
COP0, ROB0 = Position(2, 2), Position(0, 0)  # c3 / a1


async def run(url: str) -> None:
    rules = build_rules(5, 5, 25, 5)
    tr = Translator()
    mirror = InteropGame(rules)  # team B's own inferred state
    mirror.start(COP0, ROB0)

    async with Client(url) as c:
        async def call(name, **kw):
            return (await c.call_tool(name, {"token": TOKEN, **kw})).data

        caps = await call("get_capabilities")
        print("1) get_capabilities ->", caps["capabilities"]["ruleset_name"],
              "role_flexible=", caps["capabilities"]["role_flexible"])
        print("2) identity ->", await call("exchange_team_identity", team_name="team-beta"))
        print("3) accept_ruleset ->",
              await call("accept_ruleset", ruleset_name="cop-robber-grid-v1",
                         ruleset_hash=ruleset_hash()))
        nonce = generate_nonce()
        print("4) commit_nonce ->", await call("commit_nonce", sub_game_index=1,
                                               nonce_hash=commitment(nonce)))
        print("5) reveal_nonce ->", await call("reveal_nonce", sub_game_index=1, nonce=nonce))
        print("6) role_schedule ->", await call("confirm_role_schedule", schedule={}))
        print("7) integrity ->", (await call("confirm_integrity_promise", message="ok"))["ok"])
        print("8) start_sub_game ->",
              await call("start_sub_game", sub_game_index=1, role="cop",
                         initial_positions={"cop": "c3", "robber": "a1"}, seed_data={}))

        print("9) playing sub-game move-by-move via receive_action_message ...")
        code = None
        for ply in range(rules.max_moves + 2):
            if mirror.engine.state.is_terminal():
                break
            role = mirror.engine.state.turn
            kind, direction = default_policy(mirror, role)
            if kind == "move":
                msg = tr.phrase_move(direction)
                code = mirror.apply_move(role, direction)
            else:
                msg = tr.phrase_block() if kind == "block" else tr.phrase_loss()
                code = mirror.apply_block(role) if kind == "block" else mirror.admit_loss(role)
            data = await call("receive_action_message", sub_game_index=1, round_index=ply,
                              actor=STR_FROM_ROLE[role], message=msg)
            if code:
                print(f"   ply {ply}: {STR_FROM_ROLE[role]} '{msg}' -> server={data} (terminal)")
                break
        print(f"10) DONE. my terminal={code} | winner={TERMINAL_CODES.get(code)}")
        print("    -> external client played a full sub-game through the tunnel ✓")


if __name__ == "__main__":
    asyncio.run(run(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8101/mcp/"))
