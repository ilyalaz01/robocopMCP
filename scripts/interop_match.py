"""One-command bidirectional inter-team match runner (dry-run; NEVER emails).

Runs OUR interop MCP server in-process (so the opponent's calls update our shared
state), does the handshake against their server, plays 6 sub-games (our turns call
their receive_action_message; their turns arrive at our server), then saves
results/interop/report_bonus.json, prints its SHA256, and STOPS — no email.

Launch once Team B has our public URL + token (expose our port via cloudflared):

    ROBOCOP_INTEROP_TOKEN=il-nv-ai-interop-token \\
      uv run python scripts/interop_match.py <their_url> <their_token> <their_team>
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import uvicorn
from fastmcp import Client

from robocop_mcp.interop.commit_reveal import commitment, generate_nonce
from robocop_mcp.interop.constants import INTEGRITY_PROMISE
from robocop_mcp.interop.hashing import RULESET_NAME, ruleset_hash
from robocop_mcp.interop.match_runner import run_match
from robocop_mcp.interop.peer_server import make_peer_server
from robocop_mcp.interop.session import MatchSession
from robocop_mcp.interop.their_client import TheirClient

OUR_TEAM = "il-nv-ai"
OUR_TOKEN = os.environ.get("ROBOCOP_INTEROP_TOKEN", "il-nv-ai-interop-token")
PORT = int(os.environ.get("PORT", "8101"))


async def _await_opponent(game, timeout: float) -> bool:
    """Poll our shared game until the opponent's move lands (or timeout)."""
    start = game.engine.state.move_count
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        if game.engine.state.is_terminal() or game.engine.state.move_count > start:
            return True
        await asyncio.sleep(0.25)
    return False


async def _exchange_nonce(session: MatchSession, their: TheirClient, index: int) -> None:
    """Send our nonce for sub-game ``index`` and wait for theirs to reach our server."""
    nonce = generate_nonce()
    session.our_nonces[index] = nonce
    await their.commit_nonce(index, commitment(nonce))
    await their.reveal_nonce(index, nonce)
    for _ in range(240):  # wait up to ~60s for their inbound reveal
        if session.opp_nonces.get(index):
            return
        await asyncio.sleep(0.25)
    raise SystemExit(f"opponent nonce for sub-game {index} not received — is our URL/token set on their side?")


async def main(their_url: str, their_token: str, their_team: str) -> None:
    session = MatchSession(OUR_TEAM)
    session.set_opponent(their_team)
    app = make_peer_server(session, OUR_TOKEN).http_app()
    server = uvicorn.Server(uvicorn.Config(app, host="0.0.0.0", port=PORT, log_level="warning"))
    server_task = asyncio.create_task(server.serve())
    while not server.started:
        await asyncio.sleep(0.1)
    print(f"our server up on :{PORT}/mcp/  token={OUR_TOKEN}  (expose via cloudflared)")

    async with Client(their_url) as c:
        their = TheirClient(c, their_token)
        print("propose_ruleset:", await their.propose_ruleset(RULESET_NAME, ruleset_hash()))
        await their.confirm_role_schedule({"team_a": session.team_a})
        await their.confirm_integrity_promise(INTEGRITY_PROMISE)
        starts = []
        for index in range(1, 7):
            await _exchange_nonce(session, their, index)
            starts.append(session.start_positions(index))
        match_info = {"their_repo": "", "their_cop_url": their_url, "their_thief_url": their_url,
                      "their_students": []}
        await run_match(session, their, starts, _await_opponent,
                        match_info, Path("results/interop"))
    server.should_exit = True
    await server_task


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3]))
