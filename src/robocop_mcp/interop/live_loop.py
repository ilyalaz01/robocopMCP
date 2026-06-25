"""Live turn loop — the network glue that runs a sub-game over real MCP.

Each side is both MCP server and client: on its turn an agent computes its action
on its OWN inferred state and delivers it to the opponent by calling the
opponent's ``receive_action_message`` tool; the opponent parses + applies it to
its own state. No central referee. Includes the one-retry-then-loss escalation
for unclear messages (their §11.7). Proven in-process over FastMCP's in-memory
transport (and identical over HTTP for the live inter-team run).
"""

from __future__ import annotations

from fastmcp import Client

from ..constants import Role
from ..domain.models import MatchRules, Position
from .game_adapter import STR_FROM_ROLE
from .peer_server import make_peer_server
from .session import MatchSession


def _other(role: Role) -> Role:
    return Role.THIEF if role is Role.COP else Role.COP


async def _deliver(client: Client, token: str, idx: int, ply: int, actor: Role, message: str) -> dict:
    """Call the opponent's receive_action_message tool and return its data."""
    res = await client.call_tool("receive_action_message", {
        "token": token, "sub_game_index": idx, "round_index": ply,
        "actor": STR_FROM_ROLE[actor], "message": message})
    return res.data


async def run_live_sub_game(cop_session: MatchSession, rob_session: MatchSession, token: str,
                            cop: Position, robber: Position, rules: MatchRules,
                            index: int = 1) -> str | None:
    """Drive one sub-game over MCP between two interop sides; return terminal code."""
    cop_session.agent.start_sub_game(Role.COP, cop, robber, rules)
    rob_session.agent.start_sub_game(Role.THIEF, cop, robber, rules)
    sessions = {Role.COP: cop_session, Role.THIEF: rob_session}
    servers = {r: make_peer_server(s, token) for r, s in sessions.items()}

    async with Client(servers[Role.COP]) as to_cop, Client(servers[Role.THIEF]) as to_rob:
        client_to = {Role.COP: to_cop, Role.THIEF: to_rob}  # reach that role's server
        code: str | None = None
        for ply in range(rules.max_moves + 2):
            if cop_session.agent.game.engine.state.is_terminal():
                break
            actor_role = cop_session.agent.game.engine.state.turn
            actor = sessions[actor_role]
            opp = client_to[_other(actor_role)]
            if not actor.agent.game.has_legal_action(actor_role):
                code = actor.agent.game.no_legal_action_code(actor_role)
                await _deliver(opp, token, index, ply, actor_role,
                               actor.agent.translator.phrase_loss())
                break
            message, code = actor.agent.act()
            data = await _deliver(opp, token, index, ply, actor_role, message)
            if data.get("retry"):  # one retry, then the acting player loses (their §11.7)
                data = await _deliver(opp, token, index, ply, actor_role, message)
                if data.get("retry"):
                    code = f"{STR_FROM_ROLE[actor_role]}_invalid_action_retry_failed"
                    break
            if code:
                break
        return code
