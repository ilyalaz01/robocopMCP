# ADR 0001 — Tooling & repository bootstrap

**Status:** accepted · **Date:** 2026-06-25 · **Decider:** AI agent (autonomous)

## Context
The repo arrived with planning docs only (`CLAUDE.md`, `_build/`, guidelines) and was not a
git repository. The rubric mandates **uv-only**, versioned config, ≤150-LOC files, and a
committed `uv.lock`. The build runs unattended overnight.

## Decision
1. **uv only** for all dependency and task management; `pyproject.toml` is the single
   source of truth; `uv.lock` committed. `hatchling` build backend, `src/` layout.
2. **`git init` locally** and commit each phase. We do **not** configure a remote or push
   tonight (no auth; pushing unattended is out of scope) — pushing is a Phase 11 task.
3. **Build in place** in `agents_HW6/` even though the package is `robocop_mcp` and the
   eventual repo is `robocopMCP`; the directory name is cosmetic.
4. **Secrets:** the key from `claude api key.txt` is written to `.env`; both `.env` and
   `claude api key.txt` are git-ignored; `.env-example` holds a placeholder. The key is
   never exported in a shell.
5. **Coverage omits** thin entrypoints (`cli.py`, the two server mains, render-only code)
   per the rubric's allowed omissions, so coverage reflects business logic.

## Consequences
- Fully reproducible via `uv sync`; rubric-compliant tooling from commit 1.
- Morning tasks: create the GitHub remote and push; nothing else blocks on this choice.
- Alternatives rejected: Poetry/pip (forbidden by rubric); flat layout (weaker import
  isolation than `src/`).
