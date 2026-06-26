# PROGRESS LOG — robocopMCP (autonomous overnight build)

Timestamped entries per phase. Each entry: what was done, decisions (ADRs), issues,
coverage + lint status.

---

## 2026-06-25 (session 4) — Interop PlayerAgent, PRIORITY 1 ✅

**Goal:** an additive, separate "interop" agent that speaks the opponent team's pure
peer-to-peer (no-referee) protocol and REUSES our GameEngine. Solo + host-bonus untouched.
Source of truth: `_build/opponent/{assignment.md,cop_rob_game_rules.md}`.

**Done (PRIORITY 1 core)**
- `interop/constants.py`: opponent direction vocabulary (up / up-right diagonal / …),
  terminal-code table (§25), canonical ruleset name + integrity promise.
- `interop/translation.py`: `OpponentProfile` + `Translator` — chess coords (a1..e5),
  outgoing phrasing ("I move up-right diagonal."), incoming parse with **longest-match**
  direction extraction (authoritative), non-authoritative coordinate capture, block/loss/
  unclear. Profile-driven so it adapts to any opponent.
- `interop/game_adapter.py`: `InteropGame` over our `GameEngine` — the two interop deltas
  (ADR-0005): **blocks impassable to BOTH players** (`for_thief=True` for both) and **25 full
  rounds = 50 plies**; emits the opponent's exact terminal codes.
- `interop/peer_agent.py`: role-flexible `PlayerAgent` (own inferred state, legal-only
  actions, phrase/parse) + `play_sub_game` driver.
- **LOCAL PROOF (integration):** two PlayerAgents play full P2P sub-games over the message
  protocol (mocked LLM), exchanging NL actions and **agreeing on the identical terminal
  state** — no central referee. Also verified with a custom OpponentProfile (adaptation).
- 17 interop tests (translation roundtrip, blocks-both, terminal codes, self-play agreement).

**Decisions:** ADR-0005 (interop adapter reuses engine; documents the blocks-both + 50-ply
adaptations + bit-exact items) — written in PRIORITY 3.

**Gate:** ruff 0; **195 passed**; **coverage 94.8%**; all files ≤ 150 LOC. Solo/bonus untouched.

**Done (PRIORITY 2 + 3, same session)**
- `capability_handshake.py`: `our_capabilities`, `build_opponent_profile` (adapt or default to
  opponent docs), deterministic team-name role ordering (`team_order`/`role_for`, 3+3 schedule).
- `hashing.py` (canonical JSON + SHA-256 + `ruleset_hash`), `commit_reveal.py` (nonce/commit/
  verify, `derive_seed`, `seed_to_positions`) — **bit-exact, defaulted + flagged**.
- `session.py` (`MatchSession`) + `peer_tools.py` (`PeerToolService` — the opponent's EXACT 17
  tool names, token-guarded) + `peer_server.py` (FastMCP, omitted) + `config/config_interop.json`.
- ADR-0005; **`_build/INTEROP_STATUS.md`** (implemented vs bit-exact items needing opponent
  confirmation: ruleset string/hash, seed formula §5.7-vs-§7.3, seed→cell derivation, JSON
  canonicalization, opponent URLs/token). 8 protocol tests.

**Bit-exact stance (per instruction):** documented default + flag in INTEROP_STATUS, don't stop.

**Gate:** ruff 0; **203 passed**; **coverage 91.6%**; all files ≤ 150 LOC. Solo/bonus untouched.

**Note:** ~~Gmail live send timed out waiting on browser consent (no token.json); infra ready,
re-run `scripts/send_report.py` and complete consent.~~ **UPDATE 2026-06-26: RESOLVED — the solo
internal report WAS sent live via Gmail (`scripts/send_report.py`, dry_run=False); Gmail
message_id `19effc1704daaae3`, `sent: true`.** (Separate from interop.)

**Done (interop finalize — gated, never auto-send)**
- `interop/finalize.py`: after 6 sub-games, build `results/interop/report_bonus.json`
  (assignment §18.6 schema), print its **SHA256**, compare via `confirm_final_report`. Email
  is sent ONLY with explicit `--send`/`dry_run=False` AND matching hashes; **default dry-run**
  writes `email_body.txt` and sends nothing. Comparable hash EXCLUDES `mutual_agreement`.
- `confirm_final_report` now compares opponent vs our final hash; `send_final_report_email`
  tool never actually sends. `scripts/interop_finalize.py` (dry-run by default).
- 6 finalize tests (dry-run default, mismatch blocks send, send only on flag+match).
- Gate: ruff 0; **209 passed**; coverage 92.1%; files ≤ 150 LOC. Solo/bonus untouched.

## 2026-06-25 (session 3) — Strategic barriers via PBRS (ADR-0004) ✅

**Goal:** make the Cop use barriers intelligently (only when they trap) without
reward-hacking, and prove it in the logs. Additive + config-gated; solo/bonus untouched.

**Done**
- **ADR-0004**: diagnosis (no reward credit; state can't see cornering; barriers
  suboptimal on open board) + PBRS fix (policy-invariant, no spam) + honest outcome.
- **`config/config_advanced.json`** (copy of solo + `reward_shaping{enabled,weight:0.3}`,
  `enriched_cop_state`, `corner_fraction:0.3`, `qtable_dir:qtables_advanced`).
  `ConfigManager`/CLI add the `advanced` profile.
- **PBRS + enrichment + curriculum** in `learning/shaping.py` (`Phi=-(thief escape
  count)`, escape buckets, enriched cop state) and `trainer.py` (`shaping_weight`,
  `enrich_cop`, `corner_fraction` — all default OFF so solo/bonus rng/behaviour are
  byte-identical). `encode_state`/`QTable.save|load` generalized to variable-length
  state keys (2-tuple tables load unchanged). Enriched `suggest_move` wired
  (`AgentToolService.enrich`, `make_server`, SDK `qtable_dir`).
- **A/B study** (`learning/ab_barriers.py`) + notebook §7 + `assets/barrier_ab.png`.
- Advanced tables trained/saved to `results/qtables_advanced/` (+ `ab_barriers.json`).
- **Barrier demo** (`scripts/barrier_demo.py` → `results/barrier_demo/`): a scripted
  cornering sub-game over the real engine — Cop walls a cornered Thief's escape
  (escapes 3→2) and captures; transcript + PNGs.
- README subsection "Strategic barrier use via PBRS". 8 new tests.

**Honest result (the finding):** PBRS is policy-invariant, so **shaping-only matches
the baseline exactly** (100% capture, ~5 moves) and induces **zero** barrier use —
on an open 5×5 walling is genuinely suboptimal (Thief-moves-first + equal speed), so
a correct learner won't place barriers (no reward-hacking). The escape-bucket
enrichment *fragments* the table and hurts capture (76% / 47%). Per the task's
fallback, shaping stays OFF by default and the mechanic is shown via the constructed
demo. Recorded honestly in ADR-0004.

**Gate:** ruff 0 errors; **178 passed**; **coverage 95.9%**. All files ≤ 150 LOC.
Solo/bonus configs + results + qtables verified unchanged (git).

---

## 2026-06-25 (session 2) — Bonus profile + varied starts ✅

**Context:** add an inter-team "bonus" profile (open information + truthful messages) beside
the solo Dec-POMDP profile, and fix the "6 identical sub-games" defect. Driven by
`_build/SHARED_RULES.md` (provided by Ilya). Decisions: **ADR-0003** (profiles) + finalized
**ADR-0002** (host-authoritative bonus).

**Done**
- **Config profiles:** `config/config.json` (solo: `visibility=partial`, `deception=true`,
  `start_mode=seeded_random`, `start_seed=42`; negotiable narrowed to `[max_barriers,
  max_moves]`). New `config/config_bonus.json` (full/truthful, `fixed_pairs` + the 6 start
  pairs + converged 5/25 from SHARED_RULES). `ConfigManager(profile=…)` (env `ROBOCOP_PROFILE`)
  + profile-key validation.
- **Full visibility:** `build_observation(..., full=True)` returns the whole board; wired via
  `MatchRules.visibility`. **Truthful mode:** new truthful personas; `persona_for(role,
  deception)`; `LanguageEngine.deception` flag (from config).
- **Varied starts:** `domain/starts.py` (`generate_starts`: distinct seeded_random / fixed_pairs);
  orchestrator resets each sub-game to its own start. Solo now yields **6 different games**
  (3 thief / 3 cop wins) instead of 6 identical.
- **Constrained negotiation:** `valid_rules()` clamps/filters to `max_barriers∈3..8`,
  `max_moves∈{25,30}` — no invented rules. `negotiate(..., target=…)` lands the bonus on 5/25.
  Tightened the negotiator persona so even the free-text stays on barriers/moves.
- **Bonus run:** finalized ADR-0002 (host owns the session, calls remote agent over HTTP, open+
  truthful ⇒ verifiable without a referee). Integration test runs a full bonus series (both
  agents local, mocked LLM) + exact-schema bonus report.
- **Artifacts:** regenerated `results/solo_demo/` (varied, real Haiku, $0.075) and
  `results/bonus_demo/` (truthful/full-vis, $0.096); both with clean negotiation.md; events.jsonl
  saved. Removed stale `results/series_demo/`. Re-executed the notebook (0 errors). README +
  PRDs + PLAN + MORNING_BRIEF updated (P2P trust/verifiability analysis, two profiles).

**Issue fixed:** the Haiku negotiator initially wandered into invented rules (head starts, time
limits, park boundaries) in its *messages* even though the structured outcome was valid →
tightened `NEGOTIATOR_PERSONA` to discuss only barriers + move counts, regenerated dialogues.

**Gate:** ruff 0 errors; **166 passed**; **coverage 96.2%**. All files ≤ 150 LOC.

---

## 2026-06-25 — Phase 0: Scaffold, docs, config, safety ✅

**Done**
- `git init` (local only — no remote tonight; see ADR-0001). uv project initialized;
  `pyproject.toml` (ruff `E,F,W,I,N,UP,B,C4,SIM`; coverage `fail_under=85`; src layout;
  hatchling). `uv sync` OK; `uv.lock` generated.
- **Safety:** key from `claude api key.txt` → `.env`; `.env` + `claude api key.txt` +
  `*.key/*.pem/credentials.json/token.json` git-ignored; `.env-example` placeholder.
- **Config (versioned 1.00):** `config/config.json`, `config/rate_limits.json`,
  `config/logging_config.json`. `shared/config.py` (ConfigManager: load + version-validate
  + nested get), `shared/version.py`, `shared/logging_setup.py` (human log + JSONL events),
  `constants.py` (Role/Outcome/Direction enums, deltas, identity strings).
- **Docs:** `docs/PRD.md`, `docs/PLAN.md` (C4 + interfaces + ADR index), `docs/TODO.md`,
  per-mechanism PRDs (game_engine, mcp_orchestration, negotiation, q_learning,
  api_gatekeeper, reporting), `docs/PROMPTS_LOG.md`, `docs/adr/0001-tooling-and-bootstrap.md`.
  Seed `README.md` + `LICENSE` (MIT).
- **Tests:** `tests/conftest.py` (isolated temp config fixtures — no network),
  `test_config.py`, `test_logging_setup.py`.

**Decisions:** ADR-0001 (uv, local git, in-place build, secret handling, coverage omits).

**Gate:** `ruff check .` → 0 errors. `pytest --cov` → 12 passed, **coverage 95.21%**
(≥ 85%). All files ≤ 150 LOC.

**Issues:** none. Vercel session hooks are irrelevant to this Python project — ignored.

---

## 2026-06-25 — Phase 1: Game engine (pure) ✅

**Done**
- `domain/models.py` (Position, MatchRules, GameState, Observation, MoveResult,
  SubGameResult), `domain/board.py` (geometry + barrier passability),
  `domain/observation.py` (Chebyshev vision window), `domain/rules.py` (capture,
  move legality, scoring, series accumulate), `domain/engine.py` (state machine:
  thief-first turn order, capture/timeout, barrier placement forfeits move).
- 50 unit tests across models/board/observation/rules/engine incl. edge cases:
  capture on move 1, max-moves timeout = thief win, illegal/out-of-turn rejection,
  thief-may-not-STAY, barrier limit/exists/forbidden, corner off-board moves.

**Decisions:** ply = one agent action; timeout (move_count ≥ max_moves) ⇒ thief
evasion win. Barriers block only the Thief. No new ADR needed (all per SPEC §3).

**Gate:** ruff 0 errors; 50 passed; **coverage 96%** overall, domain 98-100%.
All files ≤ 150 LOC (largest: models.py 95, engine.py 94).

---

## 2026-06-25 — Phase 2: MCP servers + token auth ✅

**Done**
- `mcp/session.py`: `GameSession` (engine + NL mailbox + negotiation scratchpad),
  `SessionRegistry` singleton (`REGISTRY`) — local state-sharing mechanism (ADR-0002).
- `mcp/tools.py`: `AgentToolService` — every tool token-guarded + JSONL-logged
  (observe, read_messages, send_message, suggest_move, move, place_barrier,
  match_digest). `negotiation_tools.py`: propose/respond/confirm mixin.
- `mcp/server_app.py`: `make_server(role)` factory (DRY; Cop gets `place_barrier`,
  Thief doesn't) + `resolve_token` (env-first, revocable). Thin `cop_server.py` /
  `thief_server.py` mains (HTTP transport).
- Tests: session, tools (auth reject, illegal + out-of-turn moves, barrier rules),
  negotiation tools, server factory, **in-memory FastMCP Client integration**
  (real MCP tool calls + token rejection). Smoke-started both servers — confirmed
  listening on 127.0.0.1:8001 and :8002.

**Decisions:** ADR-0002 (in-process SessionRegistry locally; coordinator-hosted
session proposed for inter-team). Token passed as explicit tool arg (portable,
testable, works across two systems) rather than transport middleware.

**Gate:** ruff 0 errors; 80 passed; **coverage 95.7%**. All files ≤ 150 LOC.

---

## 2026-06-25 — Phase 3: Orchestrator + full local pipeline (heuristic) ✅

**Done**
- `orchestrator/turn_loop.py`: `play_turn` (observe → read → suggest → message →
  act over MCP tools) with an injectable `Decider` (heuristic now, LLM later) and
  a `default_decider`. `orchestrator/orchestrator.py`: `Orchestrator` driving the
  sub-game + 6-sub-game series loops, parameterized by cop/thief targets
  (in-memory servers now, HTTP URLs ready), with technical-loss/void re-run.
- `sdk/sdk.py`: `MarlSDK` single entry point (builds the two servers over a shared
  registry, exposes `run_series`/`run_sub_game`). CLI `--play` delegates to it.
- Integration tests: full series completes, 3×3 sub-game logs per-turn events,
  forced-void path records a void; unit tests for the decider branches.
- **Sanity runs** 2×2/3×3/4×4 → `results/sanity/` (summary.md + 81 MCP turn-event
  lines). `uv run robocop --play` runs a full 6-sub-game series over MCP.

**Decisions:** orchestrator + servers share one process/registry for local play
(per ADR-0002); targets accept in-memory servers (tests) or HTTP URLs (Phase 8).

**Gate:** ruff 0 errors; 86 passed; **coverage 95.6%**. All files ≤ 150 LOC.

---

## 2026-06-25 — Phase 4: Q-learning + heuristic baseline ✅

**Done**
- `learning/q_learning.py`: `QTable` (Bellman update, epsilon-greedy with legal-
  action masking, decay, JSON save/load), `encode_state` (clamped relative
  displacement), `action_space` (8 moves; +PLACE_BARRIER for Cop).
- `learning/trainer.py`: offline self-play (`run_episode`/`train`) on the pure
  engine with randomized starts + shaped rewards (Cop pressured to capture fast;
  Thief rewarded for surviving to timeout). Saves both tables + `learning_curve.csv`.
- `suggest_move` MCP tool now uses a trained Q-table when provided (else heuristic);
  `default_decider` handles `PLACE_BARRIER`.
- Trained canonical tables → `results/qtables/` (5000 eps, seed 0; Cop reward
  46.1→47.6, deterministic). Heuristic baseline retained in `agents/strategy.py`.

**Decisions:** state = clamped `(dx,dy)` to opponent (board-size-agnostic, small
table). Training is fully deterministic under a fixed seed → reliable convergence
test. Reward saturates on open boards (Cop captures easily); notebook (Phase 9)
will present capture-time + Q-vs-heuristic to make learning visually clear.

**Gate:** ruff 0 errors; 99 passed; **coverage 95.9%**. All files ≤ 150 LOC.

---

## 2026-06-25 — Phase 5: NL layer + API gatekeeper (real Haiku) ✅

**Done**
- `shared/gatekeeper.py`: `ApiGatekeeper` — sliding-window rate limit, FIFO queue
  with drain, backpressure (`QueueFullError`), transient retry, per-call logging
  incl. input/output token counts. Injectable clock/sleep → deterministic tests.
- `agents/persona.py`: cop/thief/negotiator/interpreter prompts (Thief is told to
  bluff). `agents/language.py`: `LanguageEngine` (generate + interpret through the
  gatekeeper, timeout + templated fallback). `agents/anthropic_client.py`: the lone
  live-SDK wiring (coverage-omitted; loads key from `.env`).
- `orchestrator.make_llm_decider`: message = real Haiku, move = Q-suggestion
  (SPEC §5 — language and movement don't fight); opponent message → logged belief.
- `reporting/transcript.py`: Markdown transcript from the JSONL stream.
- **Real Haiku sub-game** → `results/haiku_demo/transcript.md`: the Thief actively
  bluffs ("heading to the docks", "already three blocks north"); 15 API calls,
  tokens logged (e.g. 122/165/114 input tokens).

**Decisions:** every Anthropic call routes through the gatekeeper. Movement stays
deterministic (Q-table) so cost/latency are bounded and runs never hang.

**Gate:** ruff 0 errors; 119 passed; **coverage 96.0%**. All files ≤ 150 LOC.

---

## 2026-06-25 — Phase 6: Negotiation phase ✅

**Done**
- `orchestrator/negotiation.py`: `NegotiationDriver` runs propose → (counter)* →
  mutual confirm over the MCP negotiation tools. Intelligent-listener persona:
  proposes its own ruleset, argues briefly, **concedes gracefully after
  `max_rounds`** — never deadlocks. `write_negotiation_md` saves the full dialogue.
- `negotiate_respond` now adopts a counter-offer's `counter_rules` on concession.
- `language.negotiation_line` (negotiator persona). `SDK.negotiate(stance=...)`
  supports easy-agree + must-concede, applies agreed `max_barriers`/`grid_size`.
- **Real Haiku negotiation** → `results/haiku_neg/negotiation.md`: Cop argues for
  fewer barriers, Thief pushes for more; Cop concedes to 11 after 6 rounds; both
  confirm. Tests cover both paths (mocked) + grid override + md writer.

**Decisions:** structured accept/counter is a stance policy; the NL argument is
Haiku — keeps the protocol deterministic while the dialogue is free-text.

**Gate:** ruff 0 errors; 128 passed; **coverage 95.9%**. All files ≤ 150 LOC.

---

## 2026-06-25 — Phase 7: Reporting (code-ready) ✅

**Done**
- `reporting/report_builder.py`: `build_internal_report` + `build_bonus_report`
  with the assignment's EXACT field names; `count_valid`, `mcp_url`.
- `reporting/gmail_client.py`: `GmailClient` — **JSON-only** email body; `--dry-run`
  writes `results/report_internal.json` + `email_body.txt`; live send routes through
  the gatekeeper (tested with a mocked Gmail service). Live OAuth = Phase 11.
- `sdk/reporting_mixin.py`: `build_internal_report`/`build_bonus_report`/`send_report`;
  the Cop emails **only when all sub-games are valid** (else blocks with a clear error).
- 13 tests (exact schema both shapes, dry-run JSON-only, mocked live send, incomplete
  block). Generated canonical `results/report_internal.json` (totals cop 120/thief 30).

**Decisions:** body is JSON only (parseable by grader). Reporting is a mixin (one
concern). Server URLs come from config; Ilya swaps in public URLs for submission.

**Gate:** ruff 0 errors; 137 passed; **coverage 96.0%**. All files ≤ 150 LOC.

---

## 2026-06-25 — Phase 8: Full series run + artifacts ✅

**Done**
- `reporting/render.py`: matplotlib board PNGs (cop/thief/barriers) from per-ply
  `state` events (headless Agg; coverage-omitted). `reporting/summary.py`: run
  summary + token-cost at Haiku rates ($1/$5 per M). Orchestrator now logs a
  `state` event each ply.
- `scripts/run_demo.py`: one reproducible SDK-only run — negotiate → 6 sub-games
  (real Haiku) → transcript → 12 board PNGs → summary → dry-run report.
- **Artifacts in `results/series_demo/`**: transcript.md (8 KB), negotiation.md,
  12 PNGs (start/end ×6), summary.md/json, report_internal.json, email_body.txt,
  events.jsonl (360 structured events: 244 tool_call, 54 state, 48 turn, …).
- Real run: **6/6 valid**, totals cop 120 / thief 30, **124 API calls, $0.031**.

**Decisions:** logs/ stays git-ignored (regenerable); the gradeable human-readable
logs + a trimmed `events.jsonl` are committed under `results/`. Cop dominance
reflects the trained policy on an open board — Phase 9 sensitivity explores Thief-
favourable regimes.

**Gate:** ruff 0 errors; 139 passed; **coverage 96.0%**. All files ≤ 150 LOC.

---

## 2026-06-25 — Phase 9: Research notebook + graphs + cost ✅

**Done**
- `learning/experiments.py` (rollouts, `eval_stats`, `visibility_coverage`) and
  `learning/sensitivity.py` (`q_vs_heuristic`, `sensitivity_oat`) — tested helpers.
- `scripts/build_notebook.py` builds `notebooks/analysis.ipynb`; executed end-to-end
  via `nbconvert` (**0 errors**, 6 code cells with outputs).
- `assets/`: learning_curve, q_vs_heuristic, sensitivity (grid/epsilon/gamma/
  max_barriers), vision_coverage, token_cost.
- **Findings:** cop win-rate 1.0 → 0.4 as grid grows 4→6 (Thief evades more on big
  boards); ε=0.2 optimal; higher γ and more barriers favour the Cop; vision_radius
  raises observability (less reliance on language).

**Decisions:** notebooks excluded from ruff (compact analysis cells, not app code);
experiment logic lives in the tested package so the notebook stays thin + reliable.

**Gate:** ruff 0 errors; 145 passed; **coverage 95.8%**. All files ≤ 150 LOC.

---

## 2026-06-25 — Phase 10: README (scientific) + docs polish ✅

**Done**
- `README.md` (scientific): formal **Dec-POMDP model** `⟨n,S,{Aᵢ},P,R,{Ωᵢ},O,γ⟩` with
  every element defined; **orchestration-challenge analysis** (free-NL over MCP, ambiguity
  & deception with a real transcript excerpt, mutual position verification, negotiation,
  no-hang fallbacks); **results** (all 6 figures + a board screenshot + a JSONL proof of
  real MCP communication); install / usage / config / examples / structure / contributing /
  license + credits.
- Finalized `docs/TODO.md` (phases 0–10 ☑; Phase 11 hand-off list), confirmed `docs/PLAN.md`
  (C4 + ADR index), per-mechanism PRDs, and `docs/PROMPTS_LOG.md`.
- Wrote `_build/MORNING_BRIEF.md` (status + the exact 3 Phase-11 actions for Ilya).

**Gate:** ruff 0 errors; 145 passed; **coverage 95.8%**. All files ≤ 150 LOC.
No secrets tracked (verified). **Phases 0–10 complete.**
