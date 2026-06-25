"""FastMCP server exposing the interop peer tool surface over HTTP.

Thin network boundary (coverage-omitted): registers each :class:`PeerToolService`
method under the opponent's exact tool name. A PlayerAgent runs this (MCP server)
and also calls the opponent's same-named tools as an MCP client (assignment §2.4).
"""

from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.tools import Tool

from .peer_tools import PeerToolService
from .session import MatchSession

PEER_TOOLS = (
    "get_capabilities", "propose_ruleset", "accept_ruleset", "exchange_team_identity",
    "commit_nonce", "reveal_nonce", "confirm_role_schedule", "confirm_integrity_promise",
    "start_sub_game", "receive_action_message", "request_action_retry",
    "confirm_action_parse", "confirm_sub_game_result", "get_sub_game_log",
    "get_final_report", "confirm_final_report", "send_final_report_email",
)


def make_peer_server(session: MatchSession, token: str, repo_url: str = "",
                     mcp_urls: dict | None = None, students: list | None = None) -> FastMCP:
    """Build (not run) the interop FastMCP server for one match session."""
    service = PeerToolService(session, token, repo_url, mcp_urls, students)
    mcp: FastMCP = FastMCP("robocop-interop")
    for name in PEER_TOOLS:
        mcp.add_tool(Tool.from_function(getattr(service, name), name=name))
    # Additive stateless plain-JSON-RPC route for non-MCP clients (Team B); /mcp/ untouched.
    from .plain_rpc import add_plain_rpc
    add_plain_rpc(mcp, service, set(PEER_TOOLS))
    return mcp


def run_peer_server(team_name: str, token: str, host: str = "127.0.0.1",
                    port: int = 8101) -> None:  # pragma: no cover - network entry point
    """Start the interop peer server for ``team_name`` on host:port."""
    make_peer_server(MatchSession(team_name), token).run(transport="http", host=host, port=port)
