#!/usr/bin/env bash
# One-command bidirectional inter-team match: start a cloudflared tunnel to our
# in-process interop server, print our public URL + token (Team B must have these),
# then run the 6-sub-game match (dry-run; NEVER emails). Ctrl+C stops the tunnel.
#
#   ROBOCOP_INTEROP_TOKEN=il-nv-ai-interop-token \
#     bash scripts/interop_match.sh <their_url> <their_token> <their_team>
set -euo pipefail

THEIR_URL="${1:?their MCP url}"; THEIR_TOKEN="${2:?their token}"; THEIR_TEAM="${3:?their team}"
TOKEN="${ROBOCOP_INTEROP_TOKEN:-il-nv-ai-interop-token}"
PORT="${PORT:-8101}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
CF_LOG="$(mktemp)"; CF_PID=""
cleanup() { [ -n "$CF_PID" ] && kill "$CF_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

command -v cloudflared >/dev/null 2>&1 || { echo "cloudflared not found (see interop_deploy.sh)"; exit 1; }
cloudflared tunnel --url "http://localhost:$PORT" >"$CF_LOG" 2>&1 & CF_PID=$!
URL=""
for _ in $(seq 1 60); do
    URL="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$CF_LOG" | head -1 || true)"
    [ -n "$URL" ] && break; sleep 1
done
echo "=================================================================="
echo "  OUR PUBLIC URL : ${URL:-<pending>}/mcp/"
echo "  OUR TOKEN      : ${TOKEN}"
echo "  -> Team B must have these so their server can call us back."
echo "=================================================================="
ROBOCOP_INTEROP_TOKEN="$TOKEN" PORT="$PORT" \
    uv run python scripts/interop_match.py "$THEIR_URL" "$THEIR_TOKEN" "$THEIR_TEAM"
