#!/usr/bin/env bash
# One-command deploy of the interop P2P MCP agent: start the role-flexible server
# (bound on all interfaces) AND a no-account cloudflared quick tunnel, then print
# the PUBLIC MCP URL + token. Cop and Robber share this one role-flexible endpoint.
#
#   ROBOCOP_INTEROP_TOKEN=<secret> bash scripts/interop_deploy.sh
#
# Leave it running; Ctrl+C stops both the server and the tunnel.
set -euo pipefail

TOKEN="${ROBOCOP_INTEROP_TOKEN:-il-nv-ai-interop-token}"
PORT="${PORT:-8101}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
SRV_LOG="$(mktemp)"; CF_LOG="$(mktemp)"; SRV_PID=""; CF_PID=""

cleanup() { [ -n "$SRV_PID" ] && kill "$SRV_PID" 2>/dev/null || true
            [ -n "$CF_PID" ] && kill "$CF_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

# 1) interop MCP server on all interfaces
ROBOCOP_INTEROP_TOKEN="$TOKEN" uv run python scripts/interop_serve.py \
    --host 0.0.0.0 --port "$PORT" >"$SRV_LOG" 2>&1 &
SRV_PID=$!
echo "interop server starting (pid $SRV_PID) on :$PORT ..."
for _ in $(seq 1 40); do ss -ltn 2>/dev/null | grep -q ":$PORT " && break; sleep 0.5; done
if ! ss -ltn 2>/dev/null | grep -q ":$PORT "; then
    echo "ERROR: server did not bind. Log:"; tail -n 20 "$SRV_LOG"; exit 1
fi
echo "server listening on http://0.0.0.0:$PORT/mcp/"

# 2) cloudflared quick tunnel (no login required)
if ! command -v cloudflared >/dev/null 2>&1; then
    cat <<'EOF'
ERROR: cloudflared not found. Install it (no account needed), then re-run:
  # Debian/WSL:
  curl -L -o /tmp/cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
  chmod +x /tmp/cloudflared && sudo mv /tmp/cloudflared /usr/local/bin/cloudflared
  # macOS: brew install cloudflared
EOF
    exit 1
fi

cloudflared tunnel --url "http://localhost:$PORT" >"$CF_LOG" 2>&1 &
CF_PID=$!
echo "cloudflared starting (pid $CF_PID) ..."
URL=""
for _ in $(seq 1 60); do
    URL="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$CF_LOG" | head -1 || true)"
    [ -n "$URL" ] && break; sleep 1
done

echo "=================================================================="
if [ -n "$URL" ]; then
    echo "  PUBLIC MCP URL : ${URL}/mcp/"
else
    echo "  PUBLIC MCP URL : <pending> (check tunnel log: $CF_LOG)"
fi
echo "  TOKEN          : ${TOKEN}"
echo "  Cop & Robber share this one role-flexible endpoint (assignment 16.1)."
echo "  Put URL + token into _build/SHARED_RULES.md and share with the other team."
echo "=================================================================="
echo "Running. Ctrl+C to stop server + tunnel."
wait "$CF_PID"
