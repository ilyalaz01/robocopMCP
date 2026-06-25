# INTEROP STATUS — P2P inter-team agent

**What this is:** an additive interop `PlayerAgent` (`src/robocop_mcp/interop/`) that speaks the
opponent team's pure peer-to-peer protocol and **reuses our `GameEngine`**. The solo and
host-bonus systems are **untouched** and remain the graded submission. Source of truth:
`_build/opponent/{assignment.md,cop_rob_game_rules.md}` (ADR-0005).

---

## ✅ Implemented (tested, gate-green)

**PRIORITY 1 — core peer protocol + adaptive translation**
- `translation.py` — `OpponentProfile` + `Translator`: chess coords `a1..e5` (a1 bottom-left),
  opponent direction vocabulary (up / up-right diagonal / …), outgoing phrasing, incoming
  **longest-match** parsing with the declared direction authoritative and coordinates
  non-authoritative; block/loss/unclear; profile-driven so it adapts to any opponent.
- `game_adapter.py` — `InteropGame` over our `GameEngine`: blocks impassable to **both**
  players; **25 full rounds = 50 plies**; exact terminal-reason codes (their §25).
- `peer_agent.py` — role-flexible `PlayerAgent` (own inferred state) + `play_sub_game`.
- **LOCAL PROOF** (`tests/integration/test_interop_selfplay.py`): two PlayerAgents play full
  P2P sub-games over NL messages (mocked LLM) and **agree on the identical terminal state** —
  no central referee. Also passes with a custom `OpponentProfile` (adaptation).
- `capability_handshake.py` — `get_capabilities` payload + `build_opponent_profile` (adapts to
  reported capabilities; **falls back to the opponent's documented defaults** when they have no
  `get_capabilities`).

**PRIORITY 2 — rules-of-engagement parity**
- Terminal codes + illegal-action immediate-loss + no-legal-action detection (adapter).
- Deterministic **team-name role ordering** (trim/lowercase/lexicographic → Team A/B + the
  3+3 schedule; Robber moves first) — `capability_handshake.team_order` / `role_for`.
- Ruleset propose/accept (exact name+hash match or `protocol_failure`) and integrity-promise
  exchange (their canonical text) — `peer_tools.py`.
- Retry on unclear action (`receive_action_message` returns `retry=True`) — wired; the live
  one-retry-then-loss escalation runs in the turn loop (see "partial" below).

**PRIORITY 3 — bit-exact + surface**
- `hashing.py` — canonical JSON + SHA-256 (`hash_payload`, `ruleset_hash`).
- `commit_reveal.py` — nonce/commit/verify, seed derivation, seed→disjoint-cells.
- `peer_tools.py` — the **exact opponent tool names** (token-guarded): get_capabilities,
  propose_ruleset, accept_ruleset, exchange_team_identity, commit_nonce, reveal_nonce,
  confirm_role_schedule, confirm_integrity_promise, start_sub_game, receive_action_message,
  request_action_retry, confirm_action_parse, confirm_sub_game_result, get_sub_game_log,
  get_final_report, confirm_final_report, send_final_report_email.
- `peer_server.py` — FastMCP server registering all tools (network entrypoint).
- `config/config_interop.json` — interop params + the bit-exact notes + revocable token.

---

## ✅ BIT-EXACT items — CONFIRMED & aligned to Team B's spec (commit 7c583eb)

All four critical items now match Team B's confirmed spec exactly (golden tests lock them):

| Item | Implementation (bit-exact) |
| --- | --- |
| **ruleset name** | `cop-robber-grid-v1` |
| **ruleset_hash** | `a0df8e78…fc35140` = SHA-256 of `cop_rob_game_rules.md` as-is, **raw 64-hex, no prefix** (our copy hashes byte-for-byte to it) |
| **seed** | `sha256( bytes.fromhex(nonce_A) + bytes.fromhex(nonce_B) + index.to_bytes(4,"big") + ruleset_hash.lower().utf8 )` → hex. Team A nonce first. |
| **placement** | `random.Random(bytes.fromhex(seed))`; rank-major cells `a1..e5` (files faster); `cop=choice`, `robber=choice(others)` |
| **result/report hash** | `sha256( json.dumps(report, sort_keys=True, separators=(",",":")).encode() ).hexdigest()` — raw 64-hex, **no prefix**; `mutual_agreement` excluded before hashing |

Minor (consistent with the above, confirm only if their report embeds them): the commitment is
`sha256(nonce.utf8)` raw hex, and each sub-game `log_hash` uses the same raw-hex canonical hash.

## ⚠️ Other items needing Ilya / opponent before a live run
- **Opponent MCP URLs + token**, and our public URLs (deploy) — exchange checklist in
  `_build/SHARED_RULES.md`.
- **Bonus report + GATED email (implemented):** `interop/finalize.py` builds
  `results/interop/report_bonus.json` (assignment §18.6 schema + `ruleset_name/hash`,
  `role_schedule`, `seed_protocol`), prints its **SHA256**, and compares with the opponent via
  `confirm_final_report`. It **NEVER auto-sends**: default is dry-run (writes the JSON-only
  `email_body.txt`); email is sent ONLY with explicit `--send`/`dry_run=False` **AND** matching
  hashes. The comparable hash EXCLUDES `mutual_agreement` (that flag is the *result* of
  agreeing — documented default, confirm with opponent). Run: `scripts/interop_finalize.py`.
- **Live turn loop over two MCP servers** (the cross-process orchestration of
  `receive_action_message`/`confirm_action_parse` round-by-round) — the *logic* is proven by
  the in-process self-play; the cross-process driver + retry/timeout escalation is the
  remaining glue (PRIORITY 2 "partial").
- **LLM phrasing** (optional): currently a deterministic heuristic chooses the move and
  templates the message; an LLM can phrase/parse for richer logs (reuse our gatekeeper).

**Solo + host-bonus untouched and green throughout.**
