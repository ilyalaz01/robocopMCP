# TODO — robocopMCP (phased)

Status: ☐ not started · ◐ in progress · ☑ done. Owner: AI agent (autonomous), reviewed by Ilya.
DoD per phase = Verification Gate green (ruff 0, coverage ≥ 85%, files ≤ 150 LOC) + commit + log.

| # | Phase | Status | Owner | Definition of Done |
|---|-------|--------|-------|--------------------|
| 0 | Scaffold, docs, config, safety | ◐ | AI | uv works; config loads+validates; doc set exists; gate green |
| 1 | Game engine (pure) | ☐ | AI | rules + edge cases; domain coverage ≥ 90% |
| 2 | MCP servers + token auth | ☐ | AI | two HTTP servers; auth + illegal-move rejection tested |
| 3 | Orchestrator + local pipeline | ☐ | AI | full sub-game + series over HTTP (heuristic) |
| 4 | Q-learning + heuristic baseline | ☐ | AI | training converges; Q-tables saved; suggest_move wired |
| 5 | NL layer + gatekeeper | ☐ | AI | gatekeeper queue/retry; real Haiku transcript |
| 6 | Negotiation | ☐ | AI | mutual confirm; concede path; negotiation.md saved |
| 7 | Reporting (code-ready) | ☐ | AI | exact-schema JSON; mocked Gmail; --dry-run body |
| 8 | Full series run + artifacts | ☐ | AI | transcripts + PNGs + summary + report_internal.json |
| 9 | Notebook + graphs + cost | ☐ | AI | learning curves, sensitivity heatmaps, token cost |
| 10 | README (scientific) + docs polish | ☐ | AI | Dec-POMDP model; results; MORNING_BRIEF written |
| 11 | DO WITH ILYA | ☐ | Ilya | live Gmail send, cloud deploy, inter-team match |

## Cross-cutting tasks
- ☑ API key → `.env`; `.env-example`; gitignore secrets.
- ☑ Versioned config (1.00) + ConfigManager + structured logging.
- ☐ PROMPTS_LOG.md kept current with key prompts.
- ☐ Per-mechanism PRDs filled with real content by end of Phase 10.
