"""Tests for the stateless plain-JSON-RPC dispatcher + param adaptation."""

from __future__ import annotations

import asyncio

from robocop_mcp.interop.peer_server import PEER_TOOLS
from robocop_mcp.interop.peer_tools import PeerToolService
from robocop_mcp.interop.plain_rpc import adapt_args, dispatch
from robocop_mcp.interop.session import MatchSession

TOKEN = "tok"
ALLOWED = set(PEER_TOOLS)


def _disp(svc, body):
    return asyncio.run(dispatch(svc, body, ALLOWED))


def _svc() -> PeerToolService:
    s = MatchSession("il-nv-ai")
    s.set_opponent("vm__fabi")
    return PeerToolService(s, TOKEN)


def test_dispatch_direct_and_tools_call_shapes() -> None:
    svc = _svc()
    direct = _disp(svc, {"method": "get_capabilities", "params": {"auth_token": TOKEN}})
    assert direct["result"]["capabilities"]["ruleset_name"] == "cop-robber-grid-v1"
    mcp = _disp(svc, {"method": "tools/call",
                      "params": {"name": "get_capabilities", "arguments": {"auth_token": TOKEN}}})
    assert mcp["result"]["ok"] is True


def test_adapt_param_names() -> None:
    a = adapt_args("start_sub_game", {"auth_token": "t", "role": "robber",
                                      "cop_pos": "c3", "robber_pos": "a1"})
    assert a["token"] == "t" and a["initial_positions"] == {"cop": "c3", "robber": "a1"}
    b = adapt_args("confirm_role_schedule", {"schedule_json": '{"team_a":"x"}'})
    assert b["schedule"] == {"team_a": "x"}


def test_auth_and_unknown_and_bad_params() -> None:
    svc = _svc()
    bad_tok = _disp(svc, {"method": "get_capabilities", "params": {"auth_token": "WRONG"}})
    assert bad_tok["result"]["ok"] is False  # tool-level unauthorized
    unknown = _disp(svc, {"method": "no_such_tool", "params": {}})
    assert unknown["error"]["code"] == -32601
    bad = _disp(svc, {"method": "commit_nonce", "params": {"auth_token": TOKEN, "wrong": 1}})
    assert bad["error"]["code"] == -32602


def test_start_sub_game_via_rpc_stores_opponent_and_game() -> None:
    svc = _svc()
    out = _disp(svc, {"method": "start_sub_game",
                      "params": {"auth_token": TOKEN, "sub_game_index": 1, "role": "cop",
                                 "cop_pos": "c3", "robber_pos": "a1",
                                 "opponent_url": "https://x/mcp", "opponent_token": "ot"}})
    assert out["result"]["ok"] is True
    assert svc.s.agent.game is not None
    assert svc.s.opponent_url == "https://x/mcp" and svc.s.opponent_token == "ot"


def test_take_turn_no_opponent_when_no_url_anywhere(monkeypatch) -> None:
    svc = _svc()  # no opponent on session; force empty config fallback too
    monkeypatch.setattr("robocop_mcp.interop.turn_fallback.opponent_fallback",
                        lambda: (None, None))
    out = asyncio.run(svc.take_turn(TOKEN, 1, 0, "cop"))
    assert out["ok"] is False and out["error"] == "no_opponent_url"


def test_take_turn_calls_receive_action_once_no_recursion(monkeypatch) -> None:
    """One take_turn → exactly one outbound receive_action_message, never their take_turn."""
    svc = _svc()
    svc.s.opponent_url, svc.s.opponent_token = "https://x/mcp", "ot"
    calls: list[str] = []

    class FakeClient:
        def __init__(self, url, token) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def receive_action_message(self, *a):
            calls.append("receive_action_message")
            return {"terminal": None, "outcome": "ongoing"}

        async def take_turn(self, *a):  # must never be reached (would recurse)
            calls.append("take_turn")
            return {}

    monkeypatch.setattr("robocop_mcp.interop.their_client.TheirClient", FakeClient)
    out = asyncio.run(svc.take_turn(TOKEN, 1, 0, "cop"))
    assert out["ok"] is True
    assert calls == ["receive_action_message"]  # exactly one call, no recursion


def test_outcome_for_maps_terminal_reasons() -> None:
    from robocop_mcp.interop.constants import outcome_for
    assert outcome_for("cop_capture") == "cop"
    assert outcome_for("round_limit_reached") == "robber"
    assert outcome_for(None) is None


def test_receive_action_message_returns_their_format() -> None:
    """status/terminal(bool)/outcome/reason fields per Team B's contract (§25)."""
    from robocop_mcp.constants import Direction, Role
    from robocop_mcp.domain.models import Position
    svc = _svc()
    svc.s.agent.start_sub_game(Role.COP, Position(2, 2), Position(0, 0), svc.s.rules)
    msg = svc.s.agent.translator.phrase_move(Direction.N, (0, 1))  # robber a1 -> a2
    out = svc.receive_action_message(TOKEN, 1, 0, "robber", msg)
    assert out["status"] == "ack"
    assert isinstance(out["terminal"], bool)
    assert "outcome" in out and "reason" in out  # null while the game continues


def test_rpc_lists_tools_including_take_turn() -> None:
    svc = _svc()
    out = _disp(svc, {"method": "tools/list", "params": {}})
    assert "take_turn" in out["result"]["tools"]
    assert "receive_action_message" in out["result"]["tools"]
