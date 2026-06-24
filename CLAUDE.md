# robocopMCP — Claude Code Project Instructions

**This file is auto-loaded every session. Read it fully, then read `_build/SPEC.md`
and `_build/PHASES.md` before writing any code.**

---

## What this project is

Two autonomous AI agents — a **Cop** and a **Thief** — that play a partially-observable
pursuit game on a grid, **communicating in free natural language over two MCP servers**,
**negotiate their own match rules before playing**, and email a structured JSON result
report at the end.

Course: Prof. Yoram Segal, Exercise EX06 ("Dual AI Agent Race via MCP Servers").
The grade is driven by `SOFTWARE_PROJECT_GUIDELINES.md` (the rubric) — treat every
rule in it as **binding**.

**North star (this changes priorities):** the professor cares about the **orchestration
and natural-language MCP communication**, NOT about who wins or how clever the strategy
is. And he grades from **logs + README + screenshots**, because he will likely NOT run
the code himself. Therefore: **logs are the #1 deliverable.** Log everything.

---

## Autonomous overnight mode (CRITICAL)

You are running **UNATTENDED overnight**. The user (Ilya) is asleep and **cannot answer
questions**.

- **Never ask questions. Never idle waiting for input.**
- When a decision is needed: pick the option best aligned with `SOFTWARE_PROJECT_GUIDELINES.md`,
  write a short ADR in `docs/adr/NNNN-title.md`, and continue.
- Work through `_build/PHASES.md` **in order**. After each phase: run the **Verification Gate**,
  **commit**, and append a timestamped entry to `_build/PROGRESS_LOG.md`.
- Keep going until every phase's Definition of Done is met. Do **not** stop early.
  When everything in PHASES.md (except the phases explicitly marked "DO WITH ILYA") is
  done and green, write `_build/MORNING_BRIEF.md` (status + exactly what still needs Ilya)
  and then stop.
- If a real-game run or any command hangs, kill it, log the failure, and move on — never
  block the whole night on one stuck step.

---

## Verification Gate (run after every phase; ideally after every file)

1. `uv run ruff check .` → **0 errors** (fix before continuing).
2. `uv run pytest --cov` → **all tests pass, coverage ≥ 85%**.
3. Every code file ≤ **150 lines** (blank + comment-only lines excluded). If over → **split**
   it (extract helpers / mixin / constants — see `_build/SPEC.md`). NEVER compress to fit.

**Never commit code that fails the gate.**

---

## Non-negotiable rules (from the rubric)

- **uv only.** Never `pip`, `venv`, `python -m`. Use `uv add`, `uv sync`, `uv run`.
  `pyproject.toml` is the single source of truth; `uv.lock` is committed.
- **SDK is the single entry point** to all business logic. CLI / any UI only delegate to
  the SDK — **zero logic** in them.
- **API Gatekeeper:** every external call (Anthropic API, Gmail API) goes **through it**
  (rate-limit check → queue on overflow → retry → log). No direct API calls anywhere else.
- **No hard-coded values.** All game params, limits, model names, emails come from `config/`.
  Config files are **versioned** (`"version": "1.00"`).
- **No secrets in code.** See "API key setup" below.
- **TDD:** write tests with the code (RED→GREEN→REFACTOR). **Mock all external deps**
  (Anthropic API, Gmail, network). Test files also obey the 150-line rule.
- **Docstrings** on every module / class / function. Comments explain **WHY**, not what.
- **Logs are the #1 deliverable** — see `_build/SPEC.md` §Logging.

---

## Do NOT (tonight)

- Do **not** build a fancy GUI. The professor explicitly does **not** want graphics.
  A clean CLI + static board renders (matplotlib PNGs saved to `results/`) for screenshots
  is enough.
- Do **not** deploy to cloud, send live email, or attempt inter-team play tonight.
  Build them **deploy-ready** and stop at the local boundary — these are the
  "DO WITH ILYA" phases in PHASES.md.
- Do **not** over-engineer or add scope beyond SPEC + GUIDELINES.

---

## API key setup (do this first, in Phase 0)

The Anthropic API key is in the repo-root file **`claude api key.txt`** (the user put it
there deliberately). The game agents use it (model = Haiku). This repo is **PUBLIC**, so:

1. Read the key from `claude api key.txt`.
2. Write `ANTHROPIC_API_KEY=<the-key>` into **`.env`**.
3. Add **`.env`** AND **`claude api key.txt`** to **`.gitignore`** (a committed key gets
   stolen and drains the user's credit, and it tanks the rubric: "secrets in code = 0").
4. Create **`.env-example`** with `ANTHROPIC_API_KEY=your-key-here`.
5. App code loads it **process-locally** via `python-dotenv` `load_dotenv()` +
   `os.environ.get("ANTHROPIC_API_KEY")`. **You (Claude Code) must NEVER `export` this key
   in a shell command** and never put it in any shell profile — doing so would switch your
   own billing to expensive API mode. In tests, the API is mocked, so the key is not needed.

---

## Stack (locked)

Python 3.10+, **uv**, **FastMCP** (HTTP transport — two servers: cop + thief, separate ports),
**Anthropic API (`claude-haiku-4-5-20251001`) for the game agents** (language only),
**tabular Q-Learning** (numpy) for movement strategy, **pytest** (+ coverage), **ruff**,
**google-api-python-client / google-auth-oauthlib** for Gmail (code-ready, live send is a
"DO WITH ILYA" step). Each agent's brain = Haiku (language + negotiation) + Q-table (where
to move).

---

## Identity (use verbatim in reports and docs)

- Group code: **il-nv-ai**
- Students: **Ilya Lazarev** (ID 212177943), **Nadav Goldin** (ID 316350768)
- Repo: **https://github.com/ilyalaz01/robocopMCP**
- Report recipient: **rmisegal+uoh26b@gmail.com**

---

**Now read `_build/SPEC.md` (what to build) and `_build/PHASES.md` (how + the order),
then begin Phase 0.**
