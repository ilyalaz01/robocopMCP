# ADR 0002 — Authoritative state sharing across the two MCP servers

**Status:** accepted (local) / proposed (inter-team) · **Date:** 2026-06-25

## Context
Two MCP servers (Cop `:8001`, Thief `:8002`) must act on one authoritative game
state. SPEC §5 requires a `GameSession` wrapping the `GameEngine`, reachable by both
servers, and asks us to record the mechanism. For the bonus (SPEC §12) the same design
must extend to two *separate* systems.

## Decision
**Local play (tonight): an in-process `SessionRegistry` singleton.** Both servers are
started in the same Python process and share `mcp.session.REGISTRY`, a dict keyed by
`session_id`. The engine mutates exactly one `GameSession`; both role-bound
`AgentToolService` instances reference it. `move()` re-validates every claimed action
against this single source of truth ("mutual position verification"), so neither side can
desync the state.

**Inter-team play (Phase 11, proposed): a coordinator-hosted authoritative session.** The
two agents negotiate a *coordinator* (SPEC §7); the coordinator's process hosts the single
`GameSession`, and the remote agent's orchestrator calls the coordinator's MCP server over
HTTP with the shared token. Each `move()` is verified host-side before being accepted, and
`match_digest()` lets the remote side cross-check the state each turn. This keeps one
authority while both teams play, satisfying the "both email the identical JSON" rule.

## Consequences
- Local runs are simple, fast, deterministic, and fully testable without a network.
- The `AgentToolService` is transport-agnostic: the same code serves local and inter-team
  play; only *where the registry lives* changes.
- Alternatives rejected: (a) duplicated state per server with reconciliation — race-prone,
  violates single-source-of-truth; (b) external DB — over-engineered for a 6-sub-game match.
- Open item for Ilya: confirm the coordinator-hosting model with the other team after the
  lecture and once URLs/token are exchanged.
