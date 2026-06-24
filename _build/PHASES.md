# PHASES — robocopMCP build order (autonomous)

> Work top to bottom. After **every** phase: run the Verification Gate (CLAUDE.md), `git
> commit`, and append a timestamped entry to `PROGRESS_LOG.md`. Phases 0–10 are fully
> autonomous. **Phase 11 is "DO WITH ILYA" — do NOT attempt it tonight.**
>
> This order follows the professor's recommended priority table (game logic → MCP infra →
> local run → decision mechanism → natural language → [GUI demoted] → cloud → Gmail), with
> documentation first as the rubric requires.

---

## Working rules (every phase)

- **Verification Gate** must be green before commit: `uv run ruff check .` = 0 errors;
  `uv run pytest --cov` all pass + coverage ≥ 85%; every code file ≤ 150 lines.
- **TDD:** write tests with the code, mock external deps (LLM, Gmail, network).
- **Commit** with a clear message per phase (e.g. `phase 2: cop/thief MCP servers + token`).
- **Log** progress to `PROGRESS_LOG.md`: what was done, decisions (link ADRs), issues,
  current coverage + lint status. Update `docs/TODO.md` statuses.
- **Decisions:** never ask; choose per the rubric, write `docs/adr/NNNN-*.md`, continue.

---

## Phase 0 — Scaffold, docs-first, safety

**Goal:** project skeleton + all required docs + key safety + config + tooling.
**Do:**
- `uv init`; set up `pyproject.toml` (ruff config per rubric §6.1, coverage `fail_under=85`,
  deps: fastmcp, anthropic, numpy, matplotlib, google-api-python-client,
  google-auth-oauthlib, python-dotenv, pytest, pytest-cov). `uv lock`.
- **API key setup** exactly as in CLAUDE.md (read `claude api key.txt` → `.env`; gitignore
  `.env` + `claude api key.txt`; create `.env-example`). Create `.gitignore` (add `.env`,
  `*.key`, `*.pem`, `credentials.json`, `token.json`, `__pycache__`, `.venv`, `logs/`,
  `results/*.png` optional).
- Write `config/config.json`, `config/rate_limits.json`, `config/logging_config.json`
  (all versioned). Implement `shared/config.py` (load + version-validate) and
  `shared/version.py` (`__version__="1.00"`) and `shared/logging_setup.py`.
- Write the documentation set (rubric §1): `docs/PRD.md`, `docs/PLAN.md`, `docs/TODO.md`,
  the per-mechanism PRDs, and seed `docs/PROMPTS_LOG.md` (include these `_build/` files).
  These can be filled iteratively but must exist with real content by end of Phase 10.
**DoD:** `uv run` works; config loads + validates; ConfigManager tests pass; the doc files
exist with meaningful (not placeholder) content; gate green; committed.

## Phase 1 — Game engine (pure, no network)

**Goal:** authoritative rules, fully testable.
**Do:** `domain/board.py`, `domain/rules.py`, `domain/observation.py`, `domain/models.py`,
`domain/engine.py`. Implement: dynamic grid from config, 8-direction one-step moves, barrier
placement (Cop forfeits move; cell impassable to Thief; max from config), capture detection,
max-moves timeout, thief-first turn order, scoring, partial observation by `vision_radius`,
a 6-sub-game series with score accumulation, and technical-loss/void handling.
**DoD:** rich unit tests incl. edge cases (capture on move 1, barrier on occupied/edge cell,
timeout, illegal move rejected); coverage of `domain/` ≥ 90%; gate green; committed.

## Phase 2 — MCP servers + token auth (local HTTP)

**Goal:** two FastMCP servers exposing the tool set (SPEC §6) over HTTP with token auth.
**Do:** `mcp/session.py` (GameSession + SessionRegistry), `mcp/tools.py`, `mcp/cop_server.py`,
`mcp/thief_server.py`. Token required on every tool call (from `.env`/config, revocable).
`move()` enforces mutual position verification.
**DoD:** servers start on separate ports; tool-level tests (mocked transport) pass incl.
auth rejection + illegal-move rejection; gate green; committed. Record the state-sharing
mechanism in an ADR.

## Phase 3 — Orchestrator + full local pipeline (no LLM yet)

**Goal:** prove the whole pipeline end-to-end on `localhost` with a **scripted/heuristic**
agent (no LLM), so the plumbing is solid before adding language.
**Do:** `orchestrator/orchestrator.py` (parameterized by `cop_url` + `thief_url`),
`orchestrator/turn_loop.py`; a deterministic heuristic policy so a sub-game can run start to
finish over the MCP tools. Run **sanity boards 2×2, 3×3, 4×4** and save logs.
**DoD:** a full sub-game and a 6-sub-game series complete over HTTP with heuristic agents;
integration test (mocked LLM) green; sanity logs saved to `results/`; gate green; committed.

## Phase 4 — Strategy: Q-learning + heuristic baseline

**Goal:** RL depth the professor expects + the `suggest_move` tool.
**Do:** `learning/q_learning.py` (Bellman update), `learning/trainer.py` (offline self-play,
saves Cop + Thief Q-tables + reward-per-episode), `agents/strategy.py` (Q-policy + heuristic
baseline). Wire `suggest_move` to the trained table.
**DoD:** training runs headless and converges (reward trend improves); Q-tables saved;
learning-curve data saved to `results/`; tests for the update rule + policy; gate green;
committed.

## Phase 5 — Natural-language layer (Haiku via gatekeeper)

**Goal:** real free-text messages + interpretation + deception.
**Do:** `shared/gatekeeper.py` (full rubric interface: rate-limit, FIFO queue + drain,
retry, logging incl. tokens), `agents/persona.py`, `agents/language.py`. Every Anthropic
call goes through the gatekeeper. Message generation (intentions / observations / bluffs)
and interpretation (update opponent belief). Timeout + deterministic fallback so runs never
hang.
**DoD:** gatekeeper tests incl. queue-overflow + retry; language gen/parse tests with a
**mocked** LLM (deterministic); a sub-game runs with the **real** Haiku producing an actual
transcript saved to `results/`; gate green; committed.

## Phase 6 — Negotiation phase

**Goal:** the star feature — agents negotiate + confirm rules in natural language.
**Do:** `orchestrator/negotiation.py` + negotiation tools + the "intelligent listener"
persona (SPEC §7): propose own rules, argue briefly, concede gracefully after `max_rounds`,
require explicit mutual confirmation before any sub-game. Save the full dialogue to
`results/<match>/negotiation.md`.
**DoD:** negotiation reaches confirmed agreement in tests (both the "easy agree" and "must
concede" paths, mocked LLM); a real negotiated series runs with Haiku and is logged; gate
green; committed.

## Phase 7 — Reporting (code-ready; live send deferred)

**Goal:** JSON reports + Gmail sender, end-to-end provable without sending.
**Do:** `reporting/report_builder.py` (internal + bonus shapes, exact field names),
`reporting/gmail_client.py` (Gmail API, OAuth, through the gatekeeper). Cop triggers the
email on 6 valid sub-games. Body = JSON only. Provide `--dry-run` writing the body to
`results/` + logs.
**DoD:** report-builder tests validate exact schema; Gmail client tests with a **mocked**
service; `--dry-run` produces a correct `results/report_internal.json` + email body; gate
green; committed. (Live OAuth send is Phase 11.)

## Phase 8 — Full series run + artifacts

**Goal:** generate the real submission artifacts.
**Do:** run a full **negotiated 6-sub-game series on localhost with real Haiku**; produce
abundant `logs/*.jsonl`, per-sub-game transcripts, **static board PNGs** (matplotlib) for
screenshots, and a run summary (pass/fail, scores, totals, token cost). Keep API cost tiny;
log fallbacks.
**DoD:** `results/` contains a complete series: transcripts + PNGs + summary +
`report_internal.json` (dry-run); gate green; committed.

## Phase 9 — Research notebook + graphs + cost

**Goal:** rubric §8 + §10 deliverables.
**Do:** `notebooks/analysis.ipynb` — learning curves (Q vs heuristic), one-at-a-time
sensitivity heatmaps (`grid_size`, `epsilon`, `gamma`, `max_barriers`, `vision_radius`),
token-cost analysis from gatekeeper logs. Save figures to `assets/`.
**DoD:** notebook runs end-to-end; figures saved + clearly labeled; gate green; committed.

## Phase 10 — README (scientific) + docs polish

**Goal:** the graded narrative.
**Do:** write `README.md` (SPEC §16): Dec-POMDP formal model, orchestration-challenge
analysis, results + screenshots + log excerpts, install/usage/config/examples/license/
credits. Finalize `docs/PLAN.md` (C4 + ADRs + interfaces), `docs/TODO.md`, all per-mechanism
PRDs, and `docs/PROMPTS_LOG.md`. Verify every rubric §16 checkbox.
**DoD:** README + docs complete and accurate; final gate green; committed. Then write
`MORNING_BRIEF.md` (status, what's left, exactly what needs Ilya) and **stop**.

---

## Phase 11 — DO WITH ILYA (do NOT attempt tonight)

These need Ilya, external accounts, the lecture, and/or the other team:
- **Live Gmail OAuth send** — needs the browser consent flow + `credentials.json` +
  `token.json` (`google-api-installation-guide.md`).
- **Cloud deployment** — expose both MCP servers publicly (tunnel e.g. ngrok, or a cloud
  host) with the revocable token; capture the 2 public URLs.
- **Inter-team bonus match** — exchange URLs + token with the other team; finalize the
  coordination model from the ADR; run the split series; both groups email the identical
  JSON.

Leave these clearly listed in `MORNING_BRIEF.md` with the exact next actions.
