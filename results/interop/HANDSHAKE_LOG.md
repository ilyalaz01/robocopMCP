# Handshake & exchange protocol — il-nv-ai ↔️ vm__fabi

The full pre-game → play → report exchange we ran against Team B's live MCP server
(`https://cop-rob-player-agent-78e1.onrender.com/mcp`). Their server is **FastMCP
streamable-http, stateful** (requires an MCP `initialize` + `Mcp-Session-Id`, SSE
framing); the auth token is passed as the `auth_token` argument on every tool call.
We connect with the official MCP Python SDK (`streamablehttp_client → ClientSession →
initialize → call_tool`). Driver: `scripts/interop_match.py` → `interop/match_runner.py`.

All bit-exact values below were **confirmed live against their server** (their validator
accepts exactly these schemes and rejects the alternatives).

---

## 1. Capability discovery / profile

We advertise an `our_capabilities` payload (`interop/capability_handshake.py`): team
name, students, repo, MCP URLs, `ruleset_name`, `ruleset_hash`, `role_flexible: true`,
`timeout_seconds: 60`, `invalid_action_retries: 1`, `timeout_retries: 1`, 8-direction
`action_vocabulary`, `coordinate_style: chess_like`, `randomness_protocol: commit_reveal`.

Team B's server exposes no `get_capabilities`, so we fall back to their **documented
conventions** (`build_opponent_profile(None) → default_profile()`): chess coords, their
direction vocabulary, declared-direction-authoritative parsing.

## 2. Ruleset agreement — `propose_ruleset`

```
→ propose_ruleset(ruleset_name="cop-robber-grid-v1",
                  ruleset_hash="a0df8e78a545501805496d36110fa6e2850d073d72639632a3abac354fc35140")
← {"status": "accepted"}
```

`ruleset_hash` = raw lowercase 64-hex SHA-256 of `cop_rob_game_rules.md` as-is (no
`sha256:` prefix). Our copy in `_build/opponent/` hashes byte-for-byte to this. A name
or hash mismatch would `protocol_failure` and void the series.

## 3. Role schedule — `confirm_role_schedule`

Deterministic ordering `il-nv-ai < vm__fabi` → **il-nv-ai = Team A**.

```
→ confirm_role_schedule(schedule_json='{"team_a": "il-nv-ai"}')
← {"status": "confirmed"}
```

Schedule: A=Cop / B=Robber for sub-games 1–3; A=Robber / B=Cop for sub-games 4–6.

## 4. Integrity promise — `confirm_integrity_promise`

```
→ confirm_integrity_promise(message="<their canonical integrity-promise text>")
← {"status": "confirmed"}
```

## 5. Commit-reveal nonce exchange (per sub-game 1..6)

Per sub-game we generate a fresh **64-hex (32-byte)** nonce, commit it, then reveal it;
their server returns its own nonce in the reveal response.

```
→ commit_nonce(sub_game_index=i, nonce_hash=sha256(bytes.fromhex(our_nonce)).hexdigest())
← {"status": "committed"}
→ reveal_nonce(sub_game_index=i, nonce=our_nonce)            # full 64-hex value
← {"status": "verified", "nonce": "<their 64-hex nonce>"}
```

**Confirmed bit-exact (their validator):**
- **nonce length** = 64 hex chars / 32 bytes (shorter is rejected).
- **commitment** = `sha256(bytes.fromhex(nonce))` — hash of the RAW BYTES, not the hex
  string (their `reveal_nonce` returns `verified` only for this scheme).

**Seed derivation** (Team A nonce first; both sides compute the same seed):

```
seed_i = sha256( bytes.fromhex(nonce_A) + bytes.fromhex(nonce_B)
                 + i.to_bytes(4, "big") + ruleset_hash.lower().encode("utf-8") ).hexdigest()
cop    = random.Random(bytes.fromhex(seed_i)).choice(cells)     # cells = rank-major a1..e5
robber = same rng .choice([c for c in cells if c != cop])       # cop first, robber second
```

## 6. Per-sub-game play — `start_sub_game` + move exchange

```
→ start_sub_game(sub_game_index=i, role="<their role>", cop_pos="<a1..e5>", robber_pos="<a1..e5>",
                 opponent_url=<our public URL>, opponent_token=<our token>)
```

Then each round:
- **Our turn:** decide a legal action, apply to our own engine, deliver the NL message
  via `receive_action_message(sub_game_index, round_index, actor, message)` →
  `{"status","outcome","reason"}`.
- **Their turn:** pull their move synchronously with
  `choose_action(sub_game_index, round_index, actor)` → `{"message": "<their action text>"}`,
  parse it (declared direction authoritative; longest-match vocabulary; coords logged
  but non-authoritative) and apply to our engine.

Parsing fix applied here: Team B emits **short diagonal words**; our translator's
longest-match parser handles their diagonal vocabulary, which fixed an early board
desync (commit `0be270f`).

## 7. Result exchange + final report agreement

After 6 sub-games (`interop/report_exchange.py`):

```
# push our authoritative per-sub-game results
→ confirm_sub_game_result(sub_game_index=i, result_hash=<log_hash_i>,
                          result_json={sub_game_index, terminal_reason, winner_role, scores})
# pull their final report hash and compare canonically
→ confirm_final_report(report_hash=<our 393b81f3… hash>)  /  get_final_report()
```

Our `finalize()` computes the comparable hash over the report **excluding
`mutual_agreement`**, compares it to Team B's, and sets `mutual_agreement=true` on a
match. Both teams arrived at:

```
393b81f31a258c7832d6a149085820f75d0f1458a99026142eab0304f62941e2
```

## 8. Email report (gated, manual)

The agreed JSON report (`report_bonus.json` / `email_body.txt`) was emailed to
`rmisegal+uoh26b@gmail.com` by both teams:
- il-nv-ai message_id `19f015becb6345fb`
- vm__fabi message_id `19f015dc2970c0e8`

Email send is **never automatic**: it requires explicit confirmation *and* matching
report hashes (`interop/finalize.py`).

---

### Tool surface used (exact opponent tool names)

`propose_ruleset`, `confirm_role_schedule`, `confirm_integrity_promise`,
`commit_nonce`, `reveal_nonce`, `start_sub_game`, `choose_action`,
`receive_action_message`, `confirm_sub_game_result`, `confirm_final_report`,
`get_final_report`. Our side mirrors these in `interop/peer_tools.py` /
`peer_server.py` (token-guarded) so Team B's server can drive our agent symmetrically.
