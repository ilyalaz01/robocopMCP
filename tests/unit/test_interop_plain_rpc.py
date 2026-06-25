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


def test_take_turn_requires_opponent_and_game() -> None:
    svc = _svc()  # no sub-game started, no opponent url
    out = asyncio.run(svc.take_turn(TOKEN, 1, 0, "cop"))
    assert out["ok"] is False and out["error"] == "no_opponent_url"
