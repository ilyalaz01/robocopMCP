# PLAN — Architecture & Design (robocopMCP)

**Version 1.00** · C4 model + ADRs + interfaces. Read with `_build/SPEC.md`.

---

## 1. C4 — Context

```text
        ┌─────────────────────────────────────────────┐
        │             robocopMCP system               │
   ┌────┤  Cop agent  ⇄ (NL over MCP) ⇄  Thief agent  ├────┐
   │    └─────────────────────────────────────────────┘    │
   │                                                        │
 Anthropic Haiku API                                  Gmail API
 (language + negotiation,                       (report email — Cop only,
  via ApiGatekeeper)                             via ApiGatekeeper)
                                                        │
                                                   Grader inbox
                                              (rmisegal+uoh26b@gmail.com)
```

External actors: the two agents' LLM (Anthropic), the report recipient (Gmail), and — for
the bonus — a second group's MCP servers.

## 2. C4 — Container

```text
CLI (thin)
  │ delegates only
  ▼
MarlSDK ──────────────► Orchestrator (MCP client; holds the LLM + belief state)
  │                        │  HTTP + token                 │  HTTP + token
  │                        ▼                               ▼
  │                 Cop MCP server (:8001)         Thief MCP server (:8002)
  │                        \                               /
  │                         ▼                             ▼
  │                          SessionRegistry ─► GameSession ─► GameEngine
  ├──► Trainer / Q-learning (offline self-play, no network)
  ├──► ReportBuilder + GmailClient (via ApiGatekeeper)
  └──► ConfigManager + structured logging (cross-cutting)
```

## 3. C4 — Component (key modules)

- **domain/**: `board`, `rules`, `observation`, `models`, `engine` — pure, authoritative.
- **mcp/**: `session` (GameSession + SessionRegistry), `tools` (shared impls),
  `cop_server`, `thief_server` (FastMCP HTTP, token-guarded).
- **orchestrator/**: `orchestrator` (driver, parameterized by two URLs), `turn_loop`,
  `negotiation`.
- **agents/**: `persona` (prompts), `language` (gen/interpret), `strategy` (Q-policy +
  heuristic baseline).
- **learning/**: `q_learning` (Bellman), `trainer` (self-play).
- **reporting/**: `report_builder`, `gmail_client`, `render` (board PNGs).
- **shared/**: `gatekeeper`, `config`, `logging_setup`, `version`.

## 4. Key interfaces (contracts)

```text
MarlSDK.train_q_tables() -> paths
MarlSDK.negotiate(match) -> MatchRules           # mutual agreement
MarlSDK.run_sub_game(rules) -> SubGameResult
MarlSDK.run_series() -> SeriesResult
MarlSDK.build_internal_report() / build_bonus_report(...) -> dict
MarlSDK.send_report(report, dry_run=True) -> path|message_id

ApiGatekeeper.execute(api_call, *a, **kw) -> Any  # rate-limit→queue→retry→log
ApiGatekeeper.get_queue_status() -> QueueStatus

MCP tools (per server): negotiate_propose/respond/confirm, observe, read_messages,
  suggest_move, move, place_barrier (Cop), send_message, match_digest
```

## 5. Data schemas

- **Position** `(x, y)`; **Move** `(role, direction|barrier, step)`;
  **Observation** `{self, visible_cells, visible_barriers, opponent_seen?}`;
  **SubGameResult** `{outcome, moves, scores, void?}`;
  **Report** — exact field names per SPEC §11.

## 6. ADRs

Recorded under `docs/adr/`. Index:

- **0001** — Tooling & repo bootstrap (uv, git-init-local, in-place build).
- **0002** — In-process SessionRegistry for local two-server state sharing.
- (further ADRs appended as autonomous decisions are made.)

## 7. Deployment (target; Phase 11)

Both MCP servers exposed publicly via tunnel/cloud with the revocable token; two URLs
captured for the bonus. Tonight everything stops at the localhost boundary.
