"""Outbound client to the opponent's REAL MCP server (vm__fabi, confirmed).

Their ``/mcp`` is FastMCP streamable-http, STATEFUL (requires an MCP
``initialize`` handshake + ``Mcp-Session-Id``, SSE framing), with the token as the
``auth_token`` tool argument. So we call them with the official **MCP Python SDK**:
``streamablehttp_client(url) -> ClientSession -> initialize() -> call_tool(...)``.
Used as an async context manager by the match runner / take_turn tool.
"""

from __future__ import annotations

import json
from contextlib import AsyncExitStack


def _parse(result) -> dict:
    """Extract a dict from an MCP CallToolResult (structured or JSON text)."""
    sc = getattr(result, "structuredContent", None)
    if isinstance(sc, dict):
        return sc.get("result", sc) if set(sc) == {"result"} else sc
    for block in (getattr(result, "content", None) or []):
        text = getattr(block, "text", None)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"raw": text}
    return {}


class TheirClient:
    """MCP-SDK client to the opponent's stateful streamable-http ``/mcp`` server."""

    def __init__(self, url: str, token: str) -> None:
        self.url = url
        self.token = token
        self._stack: AsyncExitStack | None = None
        self.session = None

    async def __aenter__(self) -> TheirClient:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client
        self._stack = AsyncExitStack()
        read, write, _ = await self._stack.enter_async_context(streamablehttp_client(self.url))
        self.session = await self._stack.enter_async_context(ClientSession(read, write))
        await self.session.initialize()
        return self

    async def __aexit__(self, *exc) -> None:
        if self._stack:
            await self._stack.aclose()

    async def _call(self, name: str, **kw) -> dict:
        return _parse(await self.session.call_tool(name, {"auth_token": self.token, **kw}))

    async def propose_ruleset(self, name: str, ruleset_hash: str) -> dict:
        return await self._call("propose_ruleset", ruleset_name=name, ruleset_hash=ruleset_hash)

    async def commit_nonce(self, index: int, nonce_hash: str) -> dict:
        return await self._call("commit_nonce", sub_game_index=index, nonce_hash=nonce_hash)

    async def reveal_nonce(self, index: int, nonce: str) -> dict:
        return await self._call("reveal_nonce", sub_game_index=index, nonce=nonce)

    async def confirm_role_schedule(self, schedule: dict) -> dict:
        return await self._call("confirm_role_schedule", schedule_json=json.dumps(schedule))

    async def confirm_integrity_promise(self, message: str) -> dict:
        return await self._call("confirm_integrity_promise", message=message)

    async def start_sub_game(self, index: int, role: str, cop_pos: str, robber_pos: str,
                             opponent_url: str | None = None,
                             opponent_token: str | None = None) -> dict:
        kw: dict = {}
        if opponent_url:  # tell them where to push their moves (our callable server)
            kw["opponent_url"] = opponent_url
        if opponent_token:
            kw["opponent_token"] = opponent_token
        return await self._call("start_sub_game", sub_game_index=index, role=role,
                                cop_pos=cop_pos, robber_pos=robber_pos, **kw)

    async def take_turn(self, index: int, rnd: int, actor: str,
                        opponent_url: str | None = None,
                        opponent_token: str | None = None) -> dict:
        """Trigger THEIR move; their server pushes it back to our receive_action_message."""
        kw: dict = {}
        if opponent_url:
            kw["opponent_url"] = opponent_url
        if opponent_token:
            kw["opponent_token"] = opponent_token
        return await self._call("take_turn", sub_game_index=index, round_index=rnd,
                                actor=actor, **kw)

    async def choose_action(self, index: int, rnd: int, actor: str) -> dict:
        """Pull THEIR move synchronously: returns {"message": "<their action text>"}."""
        return await self._call("choose_action", sub_game_index=index,
                                round_index=rnd, actor=actor)

    async def receive_action_message(self, index: int, rnd: int, actor: str, message: str) -> dict:
        return await self._call("receive_action_message", sub_game_index=index,
                                round_index=rnd, actor=actor, message=message)

    async def confirm_sub_game_result(self, index: int, result_hash: str, result_json: dict) -> dict:
        return await self._call("confirm_sub_game_result", sub_game_index=index,
                                result_hash=result_hash, result_json=json.dumps(result_json))

    async def confirm_final_report(self, report_hash: str) -> dict:
        """Send our report hash; their server returns their hash + agreement verdict."""
        return await self._call("confirm_final_report", report_hash=report_hash)

    async def get_final_report(self) -> dict:
        """Pull the opponent's final report (so we can hash it canonically ourselves)."""
        return await self._call("get_final_report")
