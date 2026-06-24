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
