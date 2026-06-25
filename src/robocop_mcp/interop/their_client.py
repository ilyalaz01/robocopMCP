"""Outbound client to the opponent's REAL MCP server (vm__fabi interface).

Speaks their discovered wire conventions: ``auth_token`` param, JSON returned as
text content (``.data`` is null), and their exact tool names/params
(``confirm_role_schedule(schedule_json)``, ``start_sub_game(cop_pos, robber_pos)``,
``propose_ruleset`` as the ruleset agreement). Used by the match runner to deliver
our actions on our turns and to drive the pre-game handshake.
"""

from __future__ import annotations

import json


def _parse(result) -> dict:
    """Extract a dict from an opponent tool result (JSON text or structured data)."""
    text = "".join(getattr(b, "text", "") for b in (getattr(result, "content", None) or []))
    if text:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text}
    return result.data if isinstance(result.data, dict) else {"data": result.data}


class TheirClient:
    """Thin wrapper mapping our calls to the opponent's tool surface."""

    def __init__(self, client, token: str) -> None:
        self.c = client
        self.token = token

    async def _call(self, name: str, **kw) -> dict:
        return _parse(await self.c.call_tool(name, {"auth_token": self.token, **kw}))

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

    async def start_sub_game(self, index: int, role: str, cop_pos: str, robber_pos: str) -> dict:
        return await self._call("start_sub_game", sub_game_index=index, role=role,
                                cop_pos=cop_pos, robber_pos=robber_pos)

    async def receive_action_message(self, index: int, rnd: int, actor: str, message: str) -> dict:
        return await self._call("receive_action_message", sub_game_index=index,
                                round_index=rnd, actor=actor, message=message)

    async def confirm_sub_game_result(self, index: int, result_hash: str, result_json: dict) -> dict:
        return await self._call("confirm_sub_game_result", sub_game_index=index,
                                result_hash=result_hash, result_json=json.dumps(result_json))
