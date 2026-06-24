# Prompts Book — robocopMCP (rubric §7.3)

A log of the significant prompts that built this project: context, goal, outputs, and
iterative refinements. Two prompt classes: (A) the **build prompts** that directed the AI
agent to construct the repo, and (B) the **runtime prompts** (agent personas) the system
itself sends to Haiku.

---

## A. Build prompts (directing the AI agent)

### A1 — Project charter (`CLAUDE.md`)
- **Goal:** auto-loaded charter fixing north star (orchestration + NL MCP + logs), the
  unattended-overnight rules, the Verification Gate, non-negotiables (uv, SDK-first,
  gatekeeper, no secrets, TDD, ≤150 LOC), and identity strings.
- **Outcome:** every phase obeys the gate; decisions become ADRs instead of questions.

### A2 — Specification (`_build/SPEC.md`)
- **Goal:** describe WHAT to build — domain rules, config schema, layered architecture,
  MCP tool set, negotiation protocol, NL layer, Q-learning, gatekeeper, reporting, logging.
- **Refinement:** the SPEC explicitly demotes "winning" and elevates logs/README — this
  reprioritized effort toward artifacts.

### A3 — Build order (`_build/PHASES.md`)
- **Goal:** ordered phases 0–10 with per-phase Definition of Done + Verification Gate.
- **Outcome:** strictly sequential execution; commit + PROGRESS_LOG entry per phase.

> The full text of A1–A3 lives in `CLAUDE.md` and `_build/`; they are the canonical
> prompts and are reproduced there verbatim rather than duplicated here.

## B. Runtime prompts (agent personas → Haiku)
Authored in `src/robocop_mcp/agents/persona.py` (Phase 5). Recorded here once written:

- **B1 — Cop persona:** pursuer; concise tactical messages; may probe/deceive minimally.
- **B2 — Thief persona:** evader; encouraged to bluff about position (drives the
  "linguistic ambiguity" analysis in the README).
- **B3 — Negotiator persona:** intelligent, polite; proposes own ruleset, argues briefly,
  concedes gracefully after `max_rounds`.
- **B4 — Interpreter prompt:** read opponent message → estimate opponent cell (belief).

Each will be logged with goal + an example output + refinements as it is implemented and
exercised against real Haiku in Phases 5–6.

## Lessons learned (appended over the build)
- Mock all external deps in tests; keep the live LLM to a few logged turns to bound cost.
- Deterministic fallbacks make unattended runs reproducible and crash-proof.
