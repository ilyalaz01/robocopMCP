# PRD — Negotiation Protocol

**Version 1.00.** The star feature (SPEC §7). Log it in full.

## Background
Before a series, the agents talk in natural language and reach **explicit mutual
agreement** on the match. There is no third-party referee, so they must also agree who
coordinates the loop.

## What is negotiated
- **Greeting / consent** ("want to play?" → yes).
- **Coordinator** — who hosts the authoritative session (relevant for the bonus; our agent
  proposes to host and yields gracefully).
- **Rule tweaks — STRICTLY bounded (ADR-0003):** only `max_barriers ∈ 3..8` and
  `max_moves ∈ {25, 30}` may change. `valid_rules()` clamps/filters every proposal so the
  agents can **never invent undefined rules** (no time limits, head starts, "buildings",
  boundary markers, etc.). `inviolable = [thief_must_evade, turn_based, capture_ends_subgame]`
  (plus `open_information, no_deception` in the bonus profile).
- **Convergence target (bonus):** the negotiation is a brief, lively performance that lands
  on the SHARED_RULES converged values (`max_barriers 5, max_moves 25`) so two independent
  engines stay identical.
- **Explicit confirmation** — no sub-game starts until **both** call `negotiate_confirm`.

## Persona (Ilya's directive)
Intelligent, polite, well-reasoned. Proposes its own sensible ruleset first and argues
briefly, listens, seeks agreement. If the other side is intransigent after `max_rounds`,
it **concedes gracefully and plays by the other side's rules** — but always proposed first.
**Never deadlock.**

## State machine
`GREET → PROPOSE → (RESPOND/COUNTER)* → CONFIRM(both) → AGREED`. A `max_rounds` cap forces
either agreement or graceful concession. The agreed ruleset becomes the effective config.

## Outputs
Full dialogue saved to `results/<match>/negotiation.md`; structured `mutual_agreement`
object embedded in the report; every message logged to JSONL.

## Edge cases / tests
Easy-agree path; must-concede path (opponent rejects every counter to `max_rounds`);
inviolable-rule violation rejected; confirmation required from both before play.

## Success criteria
Both test paths reach a confirmed agreement; a real Haiku negotiation is logged.
