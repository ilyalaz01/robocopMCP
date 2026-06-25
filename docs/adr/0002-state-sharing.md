# ADR 0002 — Authoritative state sharing across the two MCP servers

**Status:** accepted (local + host-authoritative bonus model) · **Date:** 2026-06-25
(updated for the inter-team bonus per `_build/SHARED_RULES.md`)

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

**Inter-team play (bonus): one side HOSTS the authoritative session.** Per
`_build/SHARED_RULES.md`, the agents settle leadership during negotiation (our agent
proposes to host, yields gracefully if the other insists). The **host owns the single
`GameSession`**: it calls its own agent locally and the **remote agent via the remote public
MCP URL + the remote token**, validates every `move()` host-side, and — crucially — the
bonus runs in **full-visibility / no-deception** mode (the `bonus` profile, ADR-0003). That
combination is what makes the result *verifiable by both sides without a trusted referee*:
with open information and truthful messages there is no hidden state to lie about, so the
host's authoritative `GameSession` plus each turn's `match_digest()` cross-check are
sufficient. **The host's orchestrator produces the bonus JSON** (`build_bonus_report`, exact
schema); both teams email the byte-identical body with `mutual_agreement` set.

*Why full-visibility for the bonus (and why the solo profile stays partial+deceptive):*
under partial observation + deception, a peer could misreport hidden positions, so an
identical agreed result would require a trusted host **or** a cryptographic commit-reveal /
ZKP scheme. Open + truthful play sidesteps that entirely. The solo submission keeps the
harder Dec-POMDP (partial + deception) because there one system owns the truth.

## Consequences
- Local runs are simple, fast, deterministic, and fully testable without a network.
- The `AgentToolService` is transport-agnostic: the same code serves local and inter-team
  play; only *where the registry lives* changes.
- Alternatives rejected: (a) duplicated state per server with reconciliation — race-prone,
  violates single-source-of-truth; (b) external DB — over-engineered for a 6-sub-game match.
- Open item for Ilya: confirm the coordinator-hosting model with the other team after the
  lecture and once URLs/token are exchanged.
