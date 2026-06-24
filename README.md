# robocopMCP — Dual AI Agent Pursuit Race over MCP

> Group **il-nv-ai** · Ilya Lazarev (212177943) · Nadav Goldin (316350768)
> Course EX06 — "Dual AI Agent Race via MCP Servers" (Prof. Yoram Segal)

Two autonomous AI agents — a **Cop** and a **Thief** — play a partially-observable
pursuit game on a grid, communicating in **free natural language** over two
**MCP servers**, after **negotiating their own match rules**, and email a structured
JSON report at the end.

> **Status:** under active development. The full scientific report (Dec-POMDP model,
> orchestration analysis, results, screenshots) is completed in Phase 10 — see
> `_build/PHASES.md`. This file is the seed and will be expanded.

## Quick start

```bash
uv sync
uv run pytest          # tests (coverage >= 85%)
uv run ruff check .    # lint (0 errors)
```

## License

MIT — see `LICENSE`. Third-party credits in the final README (Phase 10).
