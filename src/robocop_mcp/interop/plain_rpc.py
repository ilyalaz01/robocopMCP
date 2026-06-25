"""Stateless plain-JSON-RPC endpoint for clients that don't speak MCP/SSE.

Team B's client sends plain JSON-RPC and chokes on our ``/mcp/`` SSE framing
("Extra data"). This adds a ``/rpc`` route that takes a plain JSON body, dispatches
to the same :class:`PeerToolService` tools (token as a body argument), and returns
**bare JSON** (no SSE, no MCP session/initialize). It adapts their param names
(``auth_token``→token, ``cop_pos``/``robber_pos``→initial_positions,
``schedule_json``→schedule). The existing ``/mcp/`` endpoint is untouched.
"""

from __future__ import annotations

import json


def adapt_args(name: str, args: dict) -> dict:
    """Map the opponent's parameter names onto our PeerToolService signatures."""
    a = dict(args)
    if "auth_token" in a:
        a.setdefault("token", a.pop("auth_token"))
    if name == "start_sub_game" and "cop_pos" in a:
        a["initial_positions"] = {"cop": a.pop("cop_pos"), "robber": a.pop("robber_pos", "")}
        a.setdefault("seed_data", a.pop("seed_data", {}))
    if name == "confirm_role_schedule" and "schedule_json" in a:
        try:
            a["schedule"] = json.loads(a.pop("schedule_json"))
        except (TypeError, json.JSONDecodeError):
            a["schedule"] = {}
    if name == "confirm_sub_game_result" and isinstance(a.get("result_json"), str):
        import contextlib
        with contextlib.suppress(json.JSONDecodeError):
            a["result_json"] = json.loads(a["result_json"])
    return a


async def dispatch(service, body: dict, allowed) -> dict:
    """Run one plain JSON-RPC call against ``service``; return a JSON-RPC result/error."""
    import inspect

    method = body.get("method")
    params = body.get("params") or {}
    if method == "tools/call":  # standard MCP shape
        name, args = params.get("name"), (params.get("arguments") or {})
    else:  # direct shape: method = tool name
        name, args = method, params
    if name not in allowed:
        return {"error": {"code": -32601, "message": f"unknown method: {name}"}}
    args = adapt_args(name, args)
    token = args.pop("token", None)
    try:
        result = getattr(service, name)(token, **args)
        if inspect.isawaitable(result):  # async tools (e.g. take_turn)
            result = await result
    except TypeError as exc:
        return {"error": {"code": -32602, "message": f"bad params for {name}: {exc}"}}
    return {"result": result}


def add_plain_rpc(mcp, service, allowed) -> None:
    """Register the ``/rpc`` stateless bare-JSON route on a FastMCP server."""
    from starlette.responses import JSONResponse

    @mcp.custom_route("/rpc", methods=["POST"])
    async def _rpc(request):
        try:
            body = await request.json()
        except Exception:  # noqa: BLE001 - malformed body
            return JSONResponse({"jsonrpc": "2.0", "id": None,
                                 "error": {"code": -32700, "message": "parse error"}},
                                status_code=400)
        out = await dispatch(service, body, allowed)
        return JSONResponse({"jsonrpc": "2.0", "id": body.get("id"), **out})
