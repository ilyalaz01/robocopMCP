"""Run the interop PlayerAgent MCP server (deploy entrypoint).

Reads host/port/token from config/config_interop.json (token overridable via the
``ROBOCOP_INTEROP_TOKEN`` env var — revocable). Use ``--host 0.0.0.0`` to expose
for a tunnel/public deployment. Both the Cop and Robber roles are served by this
one role-flexible endpoint (assignment §16.1).

    uv run python scripts/interop_serve.py                  # local 127.0.0.1:8101
    uv run python scripts/interop_serve.py --host 0.0.0.0   # bind all ifaces (tunnel)
"""

from __future__ import annotations

import argparse
import json
import os

from robocop_mcp.interop.peer_server import run_peer_server
from robocop_mcp.shared.config import ConfigManager


def main() -> None:
    cfg = json.loads((ConfigManager().root / "config" / "config_interop.json").read_text())
    srv = cfg["servers"]
    token = os.environ.get(srv["auth_token_env"]) or srv["default_token"]
    ap = argparse.ArgumentParser(prog="interop_serve")
    ap.add_argument("--host", default=srv["host"])
    ap.add_argument("--port", type=int, default=srv["port"])
    ap.add_argument("--team", default="il-nv-ai")
    args = ap.parse_args()
    print(f"interop MCP server: http://{args.host}:{args.port}/mcp/  (team {args.team})")
    run_peer_server(args.team, token, args.host, args.port)


if __name__ == "__main__":
    main()
