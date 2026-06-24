# PRD — Negotiation Protocol

**Version 1.00.** The star feature (SPEC §7). Log it in full.

## Background
Before a series, the agents talk in natural language and reach **explicit mutual
agreement** on the match. There is no third-party referee, so they must also agree who
coordinates the loop.

## What is negotiated
- **Greeting / consent** ("want to play?" → yes).
- **Coordinator** — who announces turns / drives the loop.
- **Starting positions** — shared seed or explicit cells.
- **Rule tweaks within bounds:** `negotiable = [max_barriers, grid_size, num_cops]` may
  change if BOTH agree; `inviolable = [thief_must_evade, turn_based, capture_ends_subgame]`
  must not.
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
