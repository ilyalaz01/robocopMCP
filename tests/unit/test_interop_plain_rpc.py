"""Tests for the stateless plain-JSON-RPC dispatcher + param adaptation."""

from __future__ import annotations

from robocop_mcp.interop.peer_server import PEER_TOOLS
from robocop_mcp.interop.peer_tools import PeerToolService
from robocop_mcp.interop.plain_rpc import adapt_args, dispatch
from robocop_mcp.interop.session import MatchSession

TOKEN = "tok"
ALLOWED = set(PEER_TOOLS)


def _svc() -> PeerToolService:
    s = MatchSession("il-nv-ai")
    s.set_opponent("vm__fabi")
    return PeerToolService(s, TOKEN)


def test_dispatch_direct_and_tools_call_shapes() -> None:
    svc = _svc()
    direct = dispatch(svc, {"method": "get_capabilities", "params": {"auth_token": TOKEN}}, ALLOWED)
    assert direct["result"]["capabilities"]["ruleset_name"] == "cop-robber-grid-v1"
    mcp = dispatch(svc, {"method": "tools/call",
                         "params": {"name": "get_capabilities", "arguments": {"auth_token": TOKEN}}},
                   ALLOWED)
    assert mcp["result"]["ok"] is True


def test_adapt_param_names() -> None:
    a = adapt_args("start_sub_game", {"auth_token": "t", "role": "robber",
                                      "cop_pos": "c3", "robber_pos": "a1"})
    assert a["token"] == "t" and a["initial_positions"] == {"cop": "c3", "robber": "a1"}
    b = adapt_args("confirm_role_schedule", {"schedule_json": '{"team_a":"x"}'})
    assert b["schedule"] == {"team_a": "x"}


def test_auth_and_unknown_and_bad_params() -> None:
    svc = _svc()
    bad_tok = dispatch(svc, {"method": "get_capabilities", "params": {"auth_token": "WRONG"}}, ALLOWED)
    assert bad_tok["result"]["ok"] is False  # tool-level unauthorized
    unknown = dispatch(svc, {"method": "no_such_tool", "params": {}}, ALLOWED)
    assert unknown["error"]["code"] == -32601
    bad = dispatch(svc, {"method": "commit_nonce", "params": {"auth_token": TOKEN, "wrong": 1}}, ALLOWED)
    assert bad["error"]["code"] == -32602


def test_start_sub_game_via_rpc_sets_up_game() -> None:
    svc = _svc()
    out = dispatch(svc, {"method": "start_sub_game",
                         "params": {"auth_token": TOKEN, "sub_game_index": 1, "role": "cop",
                                    "cop_pos": "c3", "robber_pos": "a1"}}, ALLOWED)
    assert out["result"]["ok"] is True
    assert svc.s.agent.game is not None
