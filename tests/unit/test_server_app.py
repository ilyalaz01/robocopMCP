"""Tests for the FastMCP server factory — tool registration + token resolution."""

from __future__ import annotations

import asyncio

from robocop_mcp.constants import Role
from robocop_mcp.mcp.server_app import make_server, resolve_token
from robocop_mcp.shared.config import ConfigManager


def _tool_names(server) -> set[str]:
    # FastMCP exposes registered tools via the async get_tool API.
    names = set()
    for name in (
        "negotiate_propose", "negotiate_respond", "negotiate_confirm", "observe",
        "read_messages", "suggest_move", "move", "send_message", "match_digest",
        "place_barrier",
    ):
        try:
            tool = asyncio.run(server.get_tool(name))
        except Exception:  # noqa: BLE001 - some versions raise instead of returning None
            tool = None
        if tool is not None:
            names.add(name)
    return names


def test_cop_server_has_place_barrier(temp_config: ConfigManager) -> None:
    server = make_server(Role.COP, token="t", config=temp_config)
    names = _tool_names(server)
    assert "place_barrier" in names
    assert "move" in names and "negotiate_confirm" in names


def test_thief_server_lacks_place_barrier(temp_config: ConfigManager) -> None:
    server = make_server(Role.THIEF, token="t", config=temp_config)
    names = _tool_names(server)
    assert "place_barrier" not in names
    assert "move" in names


def test_resolve_token_env_override(temp_config: ConfigManager, monkeypatch) -> None:
    monkeypatch.setenv("ROBOCOP_MCP_TOKEN", "rotated-token")
    assert resolve_token(temp_config) == "rotated-token"


def test_resolve_token_default(temp_config: ConfigManager, monkeypatch) -> None:
    monkeypatch.delenv("ROBOCOP_MCP_TOKEN", raising=False)
    assert resolve_token(temp_config) == "test-token"
