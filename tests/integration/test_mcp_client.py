"""Integration: a real FastMCP Client invoking tools over the MCP protocol.

Uses FastMCP's in-memory transport (no sockets) so it is fast and deterministic
while still exercising the full request/response path — proof that the servers
expose working MCP tools, not just callable Python methods. We drive the async
client via ``asyncio.run`` to avoid adding a pytest plugin dependency.
"""

from __future__ import annotations

import asyncio

import pytest
from fastmcp import Client

from robocop_mcp.constants import Role
from robocop_mcp.domain.models import MatchRules
from robocop_mcp.mcp.server_app import make_server
from robocop_mcp.mcp.session import SessionRegistry


@pytest.fixture
def cop_server(base_game_config, temp_config):
    registry = SessionRegistry()
    registry.create("demo", MatchRules.from_config(base_game_config))
    return make_server(Role.COP, token="t", registry=registry, config=temp_config)


def test_client_lists_and_calls_tools(cop_server) -> None:
    async def go():
        async with Client(cop_server) as client:
            tools = {t.name for t in await client.list_tools()}
            assert {"observe", "move", "place_barrier", "negotiate_confirm"} <= tools
            obs = await client.call_tool("observe", {"session_id": "demo", "token": "t"})
            assert obs.data["ok"] is True
            assert obs.data["observation"]["self_pos"] == [0, 0]

    asyncio.run(go())


def test_client_token_rejected(cop_server) -> None:
    async def go():
        async with Client(cop_server) as client:
            res = await client.call_tool("observe", {"session_id": "demo", "token": "WRONG"})
            assert res.data["ok"] is False
            assert "unauthorized" in res.data["error"]

    asyncio.run(go())
