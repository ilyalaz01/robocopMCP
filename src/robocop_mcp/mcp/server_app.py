"""FastMCP server factory — builds a role-specific HTTP server (SPEC §6).

Both the Cop and Thief servers are identical except that only the Cop exposes
``place_barrier``; this factory removes the duplication (rubric §3.2). The two
``*_server.py`` entry points are thin mains that call :func:`make_server` and
``run``; they are the network boundary and are excluded from coverage.
"""

from __future__ import annotations

import os

from fastmcp import FastMCP
from fastmcp.tools import Tool

from ..constants import Role
from ..shared.config import ConfigManager
from ..shared.logging_setup import setup_logging
from .session import REGISTRY, SessionRegistry
from .tools import AgentToolService

# Tool names shared by both roles; place_barrier is Cop-only and added below.
_SHARED_TOOLS = (
    "negotiate_propose", "negotiate_respond", "negotiate_confirm",
    "observe", "read_messages", "suggest_move", "move", "send_message",
    "match_digest",
)


def resolve_token(cfg: ConfigManager) -> str:
    """Read the revocable MCP token from env, falling back to config default.

    WHY env-first: rotating the token (env var) instantly revokes old clients
    without editing committed config (SPEC §6 — token is revocable).
    """
    servers = cfg.game().get("servers", {})
    env_name = servers.get("auth_token_env", "ROBOCOP_MCP_TOKEN")
    return os.environ.get(env_name) or servers.get("default_token", "change-me")


def make_server(
    role: Role,
    token: str | None = None,
    registry: SessionRegistry | None = None,
    config: ConfigManager | None = None,
    qtable=None,
) -> FastMCP:
    """Construct (but do not run) a FastMCP server for ``role``.

    Returns a configured :class:`FastMCP` with every tool the role exposes,
    each backed by a token-guarded :class:`AgentToolService`. An optional trained
    ``qtable`` makes ``suggest_move`` use the learned policy.
    """
    cfg = config or ConfigManager()
    jsonl = setup_logging(cfg)
    tok = token or resolve_token(cfg)
    service = AgentToolService(registry or REGISTRY, role, tok, jsonl, qtable=qtable)

    mcp: FastMCP = FastMCP(f"robocop-{role.value}")
    for name in _SHARED_TOOLS:
        mcp.add_tool(Tool.from_function(getattr(service, name), name=name))
    if role is Role.COP:
        mcp.add_tool(Tool.from_function(service.place_barrier, name="place_barrier"))
    return mcp


def run_server(role: Role) -> None:  # pragma: no cover - network entry point
    """Start the role's HTTP server on its configured host/port."""
    cfg = ConfigManager()
    servers = cfg.game().get("servers", {})
    host = servers[f"{role.value}_host"]
    port = servers[f"{role.value}_port"]
    make_server(role).run(transport="http", host=host, port=port)
