# SPEC — robocopMCP (what to build)

> Read this together with `SOFTWARE_PROJECT_GUIDELINES.md` (the rubric) and `PHASES.md`
> (the order). This file describes WHAT the system is. When this file and the rubric ever
> seem to conflict, the rubric wins, and you record the resolution in an ADR.

---

## 1. Mission & grading north star

Build a **complete end-to-end pipeline** where a Cop agent and a Thief agent autonomously
play a pursuit game on a grid, talking to each other in **free natural language** through
**two MCP servers**, after **negotiating their own match rules**, and the Cop emails a
JSON report at the end.

Three things matter most, in this order:
1. **Orchestration / MCP communication** — two real HTTP MCP servers, agents exchanging
   free-text messages, tools acting on the interpretation of that text. This is the point
   of the exercise.
2. **Logs + README + screenshots** — the professor grades from artifacts, not by running
   the code. Produce *abundant*, readable logs and transcripts.
3. **Rubric compliance** — every checkbox in `SOFTWARE_PROJECT_GUIDELINES.md`. Missing one
   mandatory item caps the grade at the minimum.

Strategy quality and winning are explicitly **not** the main metric. Q-Learning is included
because the professor expects to *see* RL depth and learning curves, not because winning
matters.

---

## 2. Target repository layout

```text
robocopMCP/
├── src/
│   └── robocop_mcp/
│       ├── __init__.py                 # exports public SDK; __version__
│       ├── constants.py                # enums, fixed names (no tunable values here)
│       ├── sdk/
│       │   └── sdk.py                  # MarlSDK — single entry point to ALL logic
│       ├── domain/
│       │   ├── engine.py               # GameEngine: rules, state machine (split if >150)
│       │   ├── board.py                # grid, coordinates, movement, barriers
│       │   ├── rules.py                # win/capture/scoring logic
│       │   ├── observation.py          # partial observation (vision radius)
│       │   └── models.py               # dataclasses: Position, Move, SubGameResult, ...
│       ├── orchestrator/
│       │   ├── orchestrator.py         # the MCP client / game-loop driver
│       │   ├── negotiation.py          # pre-game rule negotiation flow
│       │   └── turn_loop.py            # per-turn loop (split as needed)
│       ├── agents/
│       │   ├── persona.py              # cop / thief / negotiator system prompts
│       │   ├── language.py             # NL message generation + interpretation
│       │   └── strategy.py             # Q-table policy + heuristic baseline
│       ├── mcp/
│       │   ├── cop_server.py           # FastMCP server for the Cop (HTTP)
│       │   ├── thief_server.py         # FastMCP server for the Thief (HTTP)
│       │   ├── tools.py                # shared tool implementations
│       │   └── session.py              # authoritative GameSession + registry
│       ├── learning/
│       │   ├── q_learning.py           # tabular Q-learning + Bellman update
│       │   └── trainer.py              # self-play training loop, saves Q-tables
│       ├── reporting/
│       │   ├── report_builder.py       # internal + bonus JSON builders
│       │   └── gmail_client.py         # Gmail API sender (code-ready)
│       └── shared/
│           ├── gatekeeper.py           # ApiGatekeeper (rate-limit + queue + retry + log)
│           ├── config.py               # ConfigManager (loads + validates version)
│           ├── logging_setup.py        # structured logging config
│           └── version.py              # __version__ = "1.00"
├── tests/
│   ├── unit/                           # mirrors src/ ; mocks all external deps
│   ├── integration/                    # full local pipeline, mocked LLM
│   └── conftest.py                     # shared fixtures
├── docs/
│   ├── PRD.md
│   ├── PLAN.md                         # C4 + ADRs + interfaces
│   ├── TODO.md
│   ├── PRD_game_engine.md
│   ├── PRD_mcp_orchestration.md
│   ├── PRD_negotiation.md
│   ├── PRD_q_learning.md
│   ├── PRD_api_gatekeeper.md
│   ├── PRD_reporting.md
│   ├── PROMPTS_LOG.md                  # Prompt Engineering Log (rubric §7.3)
│   └── adr/                            # one file per decision made autonomously
├── config/
│   ├── config.json                     # all game params (versioned)
│   ├── rate_limits.json                # gatekeeper limits (versioned)
│   └── logging_config.json
├── results/                            # transcripts, board PNGs, run summaries, reports
├── logs/                               # raw structured logs (jsonl)
├── notebooks/
│   └── analysis.ipynb                  # learning curves + sensitivity + cost analysis
├── assets/                            # diagrams, screenshots referenced by README
├── README.md                          # scientific report (see §13)
├── pyproject.toml
├── uv.lock
├── .env-example
└── .gitignore
```

If any code file would exceed 150 lines, split it (the tree above already anticipates the
main split points).

---

## 3. Game domain rules (authoritative)

- **Grid:** default `[5, 5]`, read from config. Must support any size via config (no
  hard-coding). Each cell has `(x, y)` coordinates.
- **Sub-game (`sub_game`):** one pursuit round, **max 25 moves** (from config). Turn order:
  **Thief moves first, then Cop**, repeat.
- **Game / series:** **6 sub-games** (from config) played in sequence; scores accumulate.
- **Movement:** one step in any of the **8 directions** (including diagonal). Staying in
  place is allowed only if rules permit; the Thief must always be *trying to evade*
  (it may not be coded to simply stand still — that default is inviolable).
- **Cop win (capture):** Cop lands on the **exact** cell occupied by the Thief.
- **Thief win (evasion):** Thief survives the full 25 moves without being captured.
- **Barriers:** as an alternative to moving, the **Cop** may place a barrier on the cell
  it currently stands on. Placing forfeits the Cop's move that turn. The barrier cell
  becomes **impassable for the Thief** (like a wall). Max **5** barriers per sub-game
  (from config). The Thief cannot place barriers.
- **Scoring (per sub-game, all from config):**
  - Cop wins → Cop `+20`, Thief `+5`.
  - Thief wins → Cop `+5`, Thief `+10`.
- **Max series score for a group** = `3×20 + 3×10 = 90`; min `= 30`.
- **Partial observation:** each agent sees only cells within `vision_radius` (config) of
  itself (Chebyshev / Moore neighborhood). Outside that, it must **infer the opponent's
  position from natural-language messages**. This is what makes the language layer matter.
- **Technical loss:** a sub-game that fails to finish due to a technical error is **void**
  and must be re-run until 6 valid sub-games exist (log every void + re-run).

---

## 4. Config schema (`config/config.json`, versioned)

```json
{
  "version": "1.00",
  "grid_size": [5, 5],
  "max_moves": 25,
  "num_games": 6,
  "max_barriers": 5,
  "vision_radius": 1,
  "scoring": { "cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5 },
  "llm": { "model": "claude-haiku-4-5-20251001", "max_tokens": 1024, "temperature": 0.7,
           "timeout_seconds": 30 },
  "negotiation": {
    "max_rounds": 6,
    "allow_rule_changes": true,
    "negotiable": ["max_barriers", "grid_size", "num_cops"],
    "inviolable": ["thief_must_evade", "turn_based", "capture_ends_subgame"]
  },
  "q_learning": { "alpha": 0.1, "gamma": 0.9, "epsilon": 0.2, "epsilon_decay": 0.999,
                  "min_epsilon": 0.01, "episodes": 5000 },
  "report": { "recipient_email": "rmisegal+uoh26b@gmail.com", "timezone": "Asia/Jerusalem" }
}
```

`config/rate_limits.json` follows the rubric example (§4.2): `requests_per_minute`,
`requests_per_hour`, `concurrent_max`, `retry_after_seconds`, `max_retries`, plus
`max_queue_depth`. `ConfigManager` must validate `version` at load and fail clearly on
mismatch. `grid_size` / `vision_radius` etc. are the ONLY source of these values — nothing
hard-coded.

---

## 5. Architecture (layered, SDK-first)

```text
CLI (thin)  ->  SDK (single door)  ->  Orchestrator (MCP client, holds the LLM)
                                          |              |
                                          v              v
                                   Cop MCP server   Thief MCP server   (FastMCP, HTTP, token)
                                          \              /
                                           v            v
                                        GameSession  ->  GameEngine (authoritative rules)
ApiGatekeeper sits between Orchestrator/Reporting and ALL external APIs (Anthropic, Gmail).
ConfigManager + structured logging are cross-cutting.
```

- **The LLM lives in the Orchestrator (the MCP *client*), never inside an MCP server.**
  MCP servers expose **tools only**.
- **The Q-table is exposed as an MCP tool** (`suggest_move`) — this is the professor's
  "tool that computes strategy from history". Language is the LLM's job; movement strategy
  is the Q-table's job. They do not fight.
- **Authoritative state** lives in a `GameSession` (wraps `GameEngine`). Both MCP servers
  reach it through an in-process `SessionRegistry` for local play. Record the exact
  mechanism you choose in an ADR. For inter-team play see §12.
- **SDK (`MarlSDK`)** is the only entry point. Methods (at least):
  `train_q_tables()`, `negotiate(match)`, `run_sub_game(...)`, `run_series()`,
  `build_internal_report()`, `build_bonus_report(...)`, `send_report(report)`,
  `get_results()`. The CLI calls only these.

---

## 6. MCP design (the heart of the exercise)

Two FastMCP servers over **HTTP** (not stdio — even locally it must be HTTP, two servers
talking), on separate ports (e.g. cop `:8001`, thief `:8002`). Both **require a token**
(passed via header) on every tool call; the token is read from config/`.env`, is
**revocable** (change it → old clients rejected), and is the token shared with the other
team for the bonus.

**Tools — Cop server** (Thief server is identical minus `place_barrier`):

| Tool | Purpose |
| --- | --- |
| `negotiate_propose(rules, message)` | propose match rules + a natural-language message |
| `negotiate_respond(accept, counter_rules, message)` | accept / counter a proposal |
| `negotiate_confirm(message)` | final, explicit confirmation to start |
| `observe()` | partial observation within `vision_radius` + own position + visible barriers |
| `read_messages()` | the opponent's latest natural-language message(s) |
| `suggest_move()` | Q-table's recommended action for the current (encoded) state |
| `move(direction)` | validate against authoritative state, apply, return result + new observation |
| `place_barrier()` | Cop only: forfeit move, mark current cell impassable, return result |
| `send_message(text)` | post a natural-language message to the shared mailbox |
| `match_digest()` | compact authoritative snapshot for logging / mutual verification |

**Move validation = "mutual position verification":** `move()` rejects illegal claims
(teleporting, >1 step, entering a barrier, leaving the board). This is how the servers keep
both sides honest.

**Per-turn flow** (matches the professor's §5.2):
1. Orchestrator builds the active agent's context (observation + opponent's last message).
2. Orchestrator asks the agent's LLM (Haiku via the gatekeeper) for: (a) a natural-language
   message and (b) an action, exposing the agent's MCP tools to the model.
3. The model calls a tool (`suggest_move` then `move`/`place_barrier`, plus `send_message`).
4. The server validates + applies, returns the result.
5. Orchestrator logs the full exchange and advances the turn.

**Robustness for unattended runs:** every LLM call has a timeout and a **deterministic
fallback** (heuristic move + a templated message) so a real-game run never hangs. Log every
fallback.

---

## 7. Negotiation protocol (star feature — log it in full)

Before a series starts, the two agents talk in natural language and must reach explicit
mutual agreement. They negotiate:
- **Greeting / consent** ("want to play?" → yes).
- **Coordinator**: since there is no third-party referee, they agree **who announces whose
  turn / drives the loop**. (Internally our Orchestrator enforces what they agree; for
  inter-team, the agreed coordinator's orchestrator hosts — see §12.)
- **Starting positions** (a shared seed or explicit cells).
- **Rule tweaks** within bounds: items in `negotiable` may change (e.g. barriers 5→7, board
  size, even 2 cops if BOTH agree); items in `inviolable` must not (the Thief must evade,
  turn-based play, capture ends a sub-game).
- **Explicit confirmation**: no sub-game begins until **both** call `negotiate_confirm`.
  The agreed ruleset becomes the effective config for that series and is recorded in
  `mutual_agreement` / the report.

**Our agent persona (Ilya's directive):** intelligent, polite, well-reasoned. It proposes
its own (sensible) ruleset first and argues for it briefly, listens carefully, and seeks
agreement. If the other side is intransigent after `max_rounds`, it **concedes gracefully
and plays by the other side's rules** — but always proposed its own first. Never deadlock.

The entire negotiation dialogue is saved to `results/<match>/negotiation.md` and logged.

---

## 8. Natural-language layer

- **Generation:** the LLM, given the agent's persona + current observation, writes messages
  describing intentions, observations, or **deception** (bluffing about position is allowed
  and encouraged — it directly demonstrates the "linguistic ambiguity" the README must
  analyze). Cop and Thief personas differ.
- **Interpretation:** the receiving agent's LLM reads the opponent's message and updates a
  **belief** about the opponent's likely cell, which feeds the state encoding used by
  `suggest_move`.
- Keep prompts in `agents/persona.py`; keep the gen/parse functions small and testable
  (mock the LLM in tests with deterministic canned responses).

---

## 9. Q-Learning (tabular)

- **State (`s`):** a small discrete encoding — at minimum `(own_cell, believed_opponent_cell)`;
  you may use relative displacement to shrink the table. Document the encoding in
  `docs/PRD_q_learning.md`.
- **Actions (`a`):** the 8 moves (Cop also has "place barrier"). 
- **Reward (`r`):** Cop — small step penalty, large `+` on capture; Thief — small `+` per
  surviving step, large `−` on capture. Put magnitudes in config or constants and document.
- **Bellman update** (from the assignment):
  `Q(s,a) ← Q(s,a) + α · [ r + γ · max_a' Q(s',a') − Q(s,a) ]`.
- **Exploration:** epsilon-greedy with decay (params from config).
- **Training:** `trainer.py` runs **self-play episodes offline (no LLM, no network)** to
  populate **separate** Cop and Thief Q-tables, saving them to `results/` and recording
  **reward-per-episode** for the learning-curve graphs. Provide a **heuristic baseline**
  (Manhattan/Chebyshev-distance policy) for comparison in the notebook.
- The trained Q-table backs the `suggest_move` MCP tool at play time.

---

## 10. API Gatekeeper

Implement the rubric interface (§4.1): `execute(api_call, *args, **kwargs)` that checks
rate limits before every call, **queues on overflow (FIFO, max depth, backpressure, drain)
instead of dropping/crashing**, retries transient failures, and **logs every call**
(including token counts for the cost analysis). `get_queue_status()` returns depth + stats.
Limits come from `config/rate_limits.json`. **Both** the Anthropic API and the Gmail API go
through the gatekeeper. Nothing bypasses it.

---

## 11. Reporting

Two JSON shapes — use the **exact field names from the assignment**.

**Internal game report** (`results/report_internal.json`):
`group_name`, `students` (list of {id, name}), `github_repo`, `cop_mcp_url`,
`thief_mcp_url`, `timezone`, `sub_games` (list), `totals` `{cop, thief}`.

**Inter-group bonus report** (`results/report_bonus.json`):
`report_type:"bonus_game"`, `groups`{group_1, group_2}, `github_repo_group_1`,
`github_repo_group_2`, `mcp_url_group_1_cop`, `mcp_url_group_1_thief`,
`mcp_url_group_2_cop`, `mcp_url_group_2_thief`, `timezone`, `students_group_1`,
`students_group_2`, `sub_games`, `totals_by_group`, `bonus_claim`, `mutual_agreement`.

**Email:** the **Cop** agent triggers a single email to the configured recipient when all
6 sub-games are valid. Use the **Gmail API** (OAuth, token-based — see
`google-api-installation-guide.md`). **The email body contains ONLY the JSON** (no free
text), so the professor's system can parse it.

**Tonight:** write the report builders + the Gmail client fully, with **unit tests that
mock the Gmail service**. The **live OAuth send is a "DO WITH ILYA" step** (it needs a
browser auth flow + `credentials.json`). Leave a `--dry-run` that writes the email body to
`results/` and logs it, so the pipeline is provably end-to-end without sending.

---

## 12. Inter-team / bonus design (build READY, run with Ilya)

The mandatory deliverable is **one group, both agents ours**. The bonus is **two groups in
the cloud**, splitting roles: first 3 sub-games = our Cop vs their Thief; last 3 = their Cop
vs our Thief; both groups email the **identical** JSON or the bonus is void (0).

Make the core **bonus-ready** now:
- The Orchestrator is **parameterized by two server URLs** (`cop_url`, `thief_url`). For
  internal play both are ours; for the bonus, one points at the other team's server.
- Token auth + HTTP transport are already there.
- Write `docs/adr/` entries describing the chosen inter-team coordination model (who hosts /
  how the authoritative state is shared across two systems) as a **proposal** to finalize
  with Ilya after the lecture and once the other team's URLs + token exist.

Do **not** try to fully implement two-system play tonight — it depends on the lecture, the
other team, and cloud deployment.

---

## 13. Logging (the #1 deliverable — over-deliver here)

- **Structured logs** (`logs/*.jsonl`): one event per line for negotiation messages, every
  turn (agent, observation, message text, tool call, action, validation result, resulting
  state), captures, scores, every API call (model, input/output tokens, latency, cost),
  fallbacks, and errors.
- **Human-readable transcripts** per sub-game in `results/<match>/`: the full natural-language
  dialogue + the move list + the outcome. These are gold for the professor.
- **Static board renders** (matplotlib PNGs) of key frames per sub-game into `results/` —
  these are the "screenshots" the submission needs (no live GUI required).
- **Run summary** per series: pass/fail per sub-game, scores, totals, token cost.
- Make logs readable and abundant. When in doubt, log more.

---

## 14. Testing & coverage

- TDD, mirror `src/` under `tests/unit/`, full-pipeline test under `tests/integration/`
  with the **LLM and Gmail mocked** (tests must not touch the network).
- Coverage ≥ 85% enforced in `pyproject.toml` (`fail_under = 85`). `main.py`/CLI and any
  render-only code may be omitted per the rubric example.
- Cover happy paths AND error/edge cases (illegal moves, barrier on occupied cell, capture
  on first move, max-moves timeout, queue overflow in the gatekeeper, config version
  mismatch, LLM timeout → fallback).

---

## 15. Research notebook + visualizations (`notebooks/analysis.ipynb`)

- **Learning curves**: reward-per-episode for Cop and Thief (Q-learning vs heuristic
  baseline).
- **Parameter sensitivity** (rubric §8): vary `grid_size`, `epsilon`, `gamma`,
  `max_barriers`, `vision_radius` one-at-a-time; show heatmaps / line charts of win-rate
  and capture-time. Label axes, captions, legends, high resolution.
- **Token-cost analysis** (rubric §10): real token counts from the gatekeeper logs →
  cost per sub-game / series at Haiku rates ($1 / $5 per M in/out). Show the near-zero cost
  as an optimization result.
- Save all figures into `assets/` and reference them from the README.

---

## 16. Documentation deliverables (write these — rubric §1)

`README.md` (root, scientific level) must include: **formal Dec-POMDP model** — present the
pursuit as `⟨ n, S, {Aᵢ}, P, R, {Ωᵢ}, O, γ ⟩` with each element defined for this game;
**orchestration-challenge analysis** — managing free natural-language communication without
a fixed protocol, handling ambiguity and deception, ensuring mutual understanding;
**results & visualizations** — learning curves, board screenshots, CLI log excerpts proving
real MCP communication; plus install / usage / config / examples / license / credits.

Also produce, in `docs/`: `PRD.md`, `PLAN.md` (C4 Context+Container+Component diagrams as
mermaid/text, ADRs, interfaces/schemas), `TODO.md` (phased, statuses, owners, DoD), the per-
mechanism PRDs listed in the tree (§2), and `PROMPTS_LOG.md` (copy the key prompts used —
including these `_build/` files — with goal + iterations, satisfying the Prompts Book rule).
