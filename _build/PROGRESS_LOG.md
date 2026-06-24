# PROGRESS LOG — robocopMCP (autonomous overnight build)

Timestamped entries per phase. Each entry: what was done, decisions (ADRs), issues,
coverage + lint status.

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
