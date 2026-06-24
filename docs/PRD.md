# PRD — robocopMCP

**Product:** Dual AI Agent Pursuit Race over MCP
**Group:** il-nv-ai — Ilya Lazarev (212177943), Nadav Goldin (316350768)
**Course:** EX06, Prof. Yoram Segal · **Version:** 1.00

---

## 1. Overview & context

Two autonomous agents — a **Cop** and a **Thief** — play a partially-observable pursuit
game on a grid. They communicate exclusively in **free natural language** through **two
MCP servers** (one per role, HTTP transport), **negotiate their own match rules** before
play, and the Cop emails a structured JSON report when the series ends.

The exercise is an applied demonstration of **multi-agent orchestration over the Model
Context Protocol**: real servers, real tool calls, language as the coordination medium.

## 2. Problem statement

Classic pursuit-evasion assumes a shared, fixed protocol and full observability. Here each
agent sees only a `vision_radius` neighbourhood and must **infer the opponent's position
from natural-language messages** that may be honest or deliberately deceptive. The
challenge is orchestrating coherent, rule-bound play when the coordination channel is
ambiguous human-like text rather than a typed API.

## 3. Target audience

The course staff (graders). Secondary: another student group for the optional inter-team
bonus match.

## 4. Goals, KPIs, acceptance criteria

| Goal | KPI / Acceptance |
| --- | --- |
| Real MCP communication | Two HTTP FastMCP servers; token auth; tool calls logged |
| Natural-language coordination | Free-text messages generated + interpreted by Haiku |
| Rule negotiation | Explicit mutual `negotiate_confirm` before any sub-game |
| Decision mechanism | Tabular Q-learning backs `suggest_move`; learning curve improves |
| Abundant logs | `logs/*.jsonl` + transcripts + board PNGs per sub-game |
| Reporting | Exact-schema JSON; Cop emails it (dry-run locally) |
| Rubric compliance | ruff 0 errors, coverage ≥ 85%, files ≤ 150 LOC, uv-only |

## 5. Functional requirements

1. Configurable grid, max-moves, num-games, barriers, vision (all from `config/`).
2. Thief-first turn order; 8-direction moves; Cop barrier placement (≤ max, forfeits move).
3. Capture = Cop on Thief's cell; evasion = Thief survives `max_moves`.
4. Partial observation by Chebyshev radius; belief inferred from messages.
5. Pre-game negotiation with graceful concession after `max_rounds`.
6. Per-turn LLM message + action via MCP tools, with deterministic fallback on timeout.
7. Offline self-play training of Cop and Thief Q-tables.
8. Internal + bonus JSON reports; Gmail sender (code-ready, dry-run tonight).

## 6. Non-functional requirements

Reliability (never hangs — timeouts + fallbacks), Security (no secrets in code; revocable
token), Maintainability (SDK-first, ≤150-LOC files), Observability (structured logs),
Cost (Haiku; near-zero, measured by the gatekeeper). Maps to ISO/IEC 25010 (rubric §12).

## 7. Assumptions, dependencies, constraints

- Python ≥ 3.10, **uv** only. FastMCP (HTTP), Anthropic Haiku, numpy, matplotlib, Gmail API.
- Network + a valid `ANTHROPIC_API_KEY` in `.env` for live language phases (mocked in tests).
- **Out of scope (Phase 11 / with Ilya):** live Gmail OAuth send, cloud deployment,
  inter-team play. Built ready, not run, tonight.

## 8. User stories

- *As a grader*, I read the logs/transcripts and see two agents negotiating and playing in
  natural language over MCP — without running the code.
- *As the Cop agent*, when 6 valid sub-games complete, I email the JSON report.
- *As the Thief agent*, I bluff about my position to evade capture.

## 9. Timeline & deliverables

Phases 0–10 (see `_build/PHASES.md` / `docs/TODO.md`). Each phase ends green
(ruff/pytest/file-size), committed, with a `PROGRESS_LOG.md` entry. Phase 11 is deferred.
