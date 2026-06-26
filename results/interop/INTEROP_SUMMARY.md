# Interop technical history — key decisions & fixes

How our codebase was made to play a real peer-to-peer match against Team B
(vm__fabi). Full detail in `_build/INTEROP_STATUS.md` and `docs/adr/0005-interop-p2p-agent.md`.

## Design decision (ADR-0005): additive P2P adapter, one engine

Team B uses a **pure peer-to-peer** game (no central referee; each agent is both MCP
server and client; each keeps its own inferred state; commit-reveal random starts;
exact ruleset-hash agreement; result-hash confirmation). Our graded solo/host-bonus
system is **host-authoritative** and does not match this on the wire.

Decision: a **separate, additive** package `src/robocop_mcp/interop/` that speaks the
P2P protocol and **reuses our `GameEngine`** for all legality/scoring/terminal logic.
Solo and host-bonus systems are untouched and remain the graded submission.

Two interop-only rule deltas over our engine:
1. **Blocks impassable to BOTH players** (their §10.6) — the adapter computes legal
   moves with `for_thief=True` for both roles and pre-validates cop moves against
   barriers. Our base engine only blocks the Thief.
2. **25 rounds = 50 plies** — engine `max_moves = 2 × max_rounds` (a round is one
   robber action + one cop action).

## Bit-exact alignment to Team B (mismatch → series voids → 0)

Confirmed against their spec (commit `7c583eb`) and their **live** server:

| Item | Confirmed value / scheme |
| --- | --- |
| ruleset name | `cop-robber-grid-v1` |
| ruleset_hash | `a0df8e78…fc35140` = raw 64-hex SHA-256 of `cop_rob_game_rules.md`, no prefix |
| nonce length | 64 hex chars (32 bytes) — shorter rejected by their `reveal_nonce` |
| commitment | `sha256(bytes.fromhex(nonce))` — hash of RAW BYTES, not the hex string |
| seed | `sha256(bytes(nonce_A) + bytes(nonce_B) + i.to_bytes(4,"big") + ruleset_hash.utf8)`; Team A nonce first |
| placement | `random.Random(bytes.fromhex(seed))`; rank-major `a1..e5`; cop=choice, robber=choice(others) |
| report hash | `sha256(json.dumps(report, sort_keys=True, separators=(",",":")))`, raw 64-hex; `mutual_agreement` excluded |

Earlier we held a different documented default (nonce as hex string, `sha256:` prefix,
seed via UTF-8 concat); these were corrected once Team B's server confirmed the real
schemes (commits `2037be9`, `7c583eb`, `aab3bb7`).

## Key fixes during live bring-up

- **P2P adapter over our engine** (`game_adapter.py`, `peer_agent.py`) + in-process
  self-play proof: two `PlayerAgent`s play full P2P sub-games over NL and agree on an
  identical terminal state with no referee (`5e50cb8`, `5fb6d91`).
- **Their endpoint is stateful `/mcp` (FastMCP streamable-http)** — switched our
  outbound client to the official MCP Python SDK with `initialize` + session id; auth
  via `auth_token` tool argument; responses arrive as JSON text content (`their_client.py`).
- **Commit-reveal alignment** — nonce length + raw-bytes commitment matched to their
  validator (`2037be9`).
- **Coordinator match via synchronous nonce + `choose_action` pull** — their server
  records our data but returns only status, so turns are driven by pulling their move
  with `choose_action` instead of awaiting an async push (`b8c5c99`).
- **Short-diagonal parse fix** — their diagonal move words are short; the translator's
  longest-match parser with declared-direction-authoritative resolution fixed the root
  cause of an early board desync (`0be270f`).
- **Final report-hash exchange** — push our per-sub-game results via
  `confirm_sub_game_result`, pull their report hash via `confirm_final_report` /
  `get_final_report`, compare canonically (`3a657bd`).
- **Agreed bonus report + gated live send** — on matching hashes set
  `mutual_agreement=true`; email only on explicit confirmation (`aa20294`).

## Verification

The interop package ships with unit + integration tests (translation roundtrip,
blocks-both, terminal codes, commit-reveal, plain-RPC, report exchange, finalize
gating, in-process self-play agreement). Solo + host-bonus systems verified unchanged
throughout. See `_build/PROGRESS_LOG.md` for the gate results per session.
