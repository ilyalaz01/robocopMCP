# ADR 0005 — Additive interop PlayerAgent for the P2P inter-team match

**Status:** accepted · **Date:** 2026-06-25 · **Decider:** AI agent (autonomous)

## Context
The opponent team uses a **pure peer-to-peer correspondence game** (no central referee; each
agent is both MCP server and MCP client; each maintains its own inferred state; full
observability; strict honesty; commit-reveal random starts; exact ruleset-hash agreement;
result-hash confirmation). Our existing system is **host-authoritative** and does not match
this on the wire. Source of truth: `_build/opponent/{assignment.md,cop_rob_game_rules.md}`.

## Decision
A **separate, additive** package `src/robocop_mcp/interop/` (new profile
`config/config_interop.json`, new server entrypoint) that speaks the P2P protocol and
**reuses our `GameEngine`** for all legality, scoring, terminal detection, and state. The
solo and host-bonus systems are untouched and remain the graded submission.

**Two interop-specific adaptations over our engine** (the only game-rule differences):
1. **Blocks impassable to BOTH players.** Their §10.6 blocks block cop *and* robber; our
   engine blocks only the Thief. The interop adapter computes legal moves with
   `for_thief=True` for both roles and pre-validates Cop moves against barriers, so we never
   feed the engine an into-barrier Cop move.
2. **25 full rounds = 50 plies.** Their "25 moves" = 25 robber + 25 cop actions; we set the
   engine's `max_moves = 2 × max_rounds`.

**Adaptive translation.** A capability handshake builds an `OpponentProfile` (direction
vocabulary, coordinate notation, phrasing, timeout); it **defaults to the opponent team's
documented conventions** so it works out-of-the-box with them and adapts to any other team.
The declared **direction is authoritative**; coordinates are non-authoritative (logged only).

## Bit-exact items (DEFAULTED + FLAGGED — see `_build/INTEROP_STATUS.md`)
Per the instruction "don't stop on unclear bit-exact points: set a documented default, flag,
and continue," each of these uses a documented default and **must be confirmed bit-exact with
the opponent or the series voids (hash mismatch → 0)**:
- **ruleset canonical string + hash** — we hash the fixed official ruleset object as
  `sha256:<sha256(canonical_json)>` with `sort_keys=True`, separators `(",",":")`, UTF-8.
- **commit-reveal seed** — `SHA256(nonce_A || nonce_B || str(i) || ruleset_hash)` (the variant
  WITH `ruleset_hash`; assignment §5.7 omits it — flagged). `||` = UTF-8 string concat.
- **seed→cell** — walk the seed hex over cells in coordinate order `a1,b1,…`; index
  `k → (k%w, k//w)`; resample the Robber until disjoint.
- **result/report hashing** — same canonical-JSON + SHA-256.

## Consequences
- The same `GameEngine` powers solo, host-bonus, and interop — one source of legality.
- Honest negative-risk surfaced loudly: any bit-exact mismatch voids the bonus; these are the
  items to confirm with the opponent before a live run.
- Alternatives rejected: rewriting our system to be P2P (violates "do not modify solo/bonus");
  a second engine (duplicates legality logic).
