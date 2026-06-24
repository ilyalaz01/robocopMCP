# PRD — MCP Servers & Orchestration

**Version 1.00.** The heart of the exercise (SPEC §6).

## Background
Two **FastMCP** servers over **HTTP** (cop `:8001`, thief `:8002`), each exposing the
agent's tools. The **LLM lives only in the orchestrator (the MCP client)** — servers expose
**tools, never a model**. Authoritative state is a `GameSession` reached via an in-process
`SessionRegistry` (ADR-0002).

## Tools (Cop; Thief identical minus `place_barrier`)
`negotiate_propose`, `negotiate_respond`, `negotiate_confirm`, `observe`, `read_messages`,
`suggest_move`, `move`, `place_barrier`, `send_message`, `match_digest`.

## Security
Every tool call requires a **token** (header), read from `.env`/config, **revocable**
(rotate → old clients rejected). Same token is shared with the other team for the bonus.

## Mutual position verification
`move()` validates each claimed action against authoritative state (no teleport, ≤1 step,
not into a barrier, on-board). This keeps two independent systems honest in inter-team play.

## Per-turn flow
1. Orchestrator builds context (observation + opponent's last message).
2. Asks the agent's LLM (Haiku via gatekeeper) for a message + an action, exposing tools.
3. Model calls `suggest_move` → `move`/`place_barrier`, plus `send_message`.
4. Server validates + applies; returns result + new observation.
5. Orchestrator logs the full exchange and advances the turn.

## Robustness
Every LLM call has a timeout and a **deterministic fallback** (heuristic move + templated
message) so unattended runs never hang. Every fallback is logged.

## Inter-team readiness (Phase 11)
Orchestrator is parameterized by `cop_url` + `thief_url`; for the bonus one URL points at
the other team's server. Coordination model proposed in ADR.

## Success criteria
Servers start on separate ports; auth rejection + illegal-move rejection tested; a full
sub-game runs over HTTP.
