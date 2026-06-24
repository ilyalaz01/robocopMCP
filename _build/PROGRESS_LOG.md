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
