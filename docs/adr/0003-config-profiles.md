# ADR 0003 — Config profiles (solo vs bonus) + visibility/deception/starts

**Status:** accepted · **Date:** 2026-06-25 · **Decider:** AI agent (autonomous)

## Context
The solo submission is a true Dec-POMDP (partial observation + deception allowed) and must
stay as-is. The inter-team **bonus** match, per `_build/SHARED_RULES.md`, requires the
opposite: **open information + truthful messages** (the only refereeable basis for two
independent systems to compute an identical result). We also had a visible defect: all 6
sub-games were identical because both players always started in the same corners and the
trained Q-policy is deterministic — the same game replayed six times.

## Decision
1. **Two config profiles**, both versioned `"1.00"`, selected by `ConfigManager(profile=…)`
   (default `solo`), overridable by the `ROBOCOP_PROFILE` env var / a `--profile` CLI flag:
   - `config/config.json` (**solo**): `visibility="partial"`, `deception=true`,
     `vision_radius=1`, `start_mode="seeded_random"`, `start_seed=42`.
   - `config/config_bonus.json` (**bonus**): `visibility="full"`, `deception=false`,
     `start_mode="fixed_pairs"`, the **6 start pairs and converged negotiable values
     (max_barriers 5, max_moves 25) taken verbatim from `_build/SHARED_RULES.md`**.
2. **Visibility** is config-driven in `observe()`: `full` returns the complete board (both
   positions + all barriers); `partial` keeps the Chebyshev `vision_radius` window.
3. **Deception** is config-driven in the persona: `deception=false` switches to a truthful
   persona that may never state a false position or intent.
4. **Varied starts** fix the identical-games defect: `seeded_random` derives 6 distinct,
   non-overlapping pairs from `start_seed` (reproducible); `fixed_pairs` reads the explicit
   table so two independent codebases get byte-identical starts.
5. **Negotiation is constrained** to `{max_barriers ∈ 3..8, max_moves ∈ {25,30}}` only — no
   invented rules. The bonus negotiation is a brief performance that lands on 5 / 25.

## Consequences
- The solo Dec-POMDP framing is untouched; the bonus profile is additive.
- The same engine/orchestrator/SDK serve both profiles — only data changes (rubric §6.2).
- The 6 sub-games now differ (distinct starts → distinct trajectories and move counts).
- Alternatives rejected: a single profile with runtime flags (muddier config + tests);
  keeping deception in the bonus match (un-refereeable across two systems — see ADR-0002).
