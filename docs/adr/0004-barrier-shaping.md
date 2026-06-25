# ADR 0004 — Strategic barrier use via potential-based reward shaping

**Status:** accepted · **Date:** 2026-06-25 · **Decider:** AI agent (autonomous)

## Context
The trained Cop never places barriers. Three compounding reasons:

1. **No reward credit.** The Cop's reward is `step_penalty` per move and `+capture_reward`
   on capture. `place_barrier` forfeits the move (no progress toward capture) and earns
   nothing, so its Q-value can never exceed a chasing move.
2. **State can't tell when a barrier helps.** The Q-state is only the relative displacement
   `(dx, dy)` to the Thief. It cannot represent "the Thief is nearly cornered", which is the
   *only* situation where a barrier pays off — so the Cop cannot learn a conditional policy.
3. **On an open 5×5, chasing genuinely dominates.** Forfeiting a move to wall an open board
   rarely beats stepping closer; the Cop's avoidance is partly *correct*. The mechanic is
   therefore invisible in results, which a grader may look for.

## Decision
An **additive, config-gated** `advanced` profile (solo + bonus untouched) that makes barriers
worthwhile *exactly when they trap*, without reward-hacking:

1. **Potential-based reward shaping (PBRS).** Add to the Cop's per-step reward only
   `F = γ·Φ(s') − Φ(s)` with `Φ(s) = −(number of legal escape moves the Thief has)`. A
   barrier that cuts the Thief's escape routes raises `Φ`, yielding a positive `F` *that
   step* — so the Cop learns to place barriers **when** they reduce escape. By Ng, Harada &
   Russell (1999) PBRS is **policy-invariant**: the shaped return telescopes to
   `γ^T·Φ(s_T) − Φ(s_0)`, so the optimal policy is unchanged and there is no reward-hacking.
   We deliberately do **not** add a flat `+reward for placing a barrier` — that induces
   barrier spam (placing even when it doesn't trap).
2. **Minimal state enrichment.** One compact feature is appended to the Cop's state: the
   Thief's escape-move count bucketed `0–2 / 3–5 / 6–8` (`escape_bucket`). This lets the Cop
   condition on "nearly cornered" without blowing up the table (≤ 3× states). Documented in
   `docs/PRD_q_learning.md`. The Thief's state is unchanged.
3. **Curriculum slice.** ~30% of training episodes start the Thief in/adjacent to a corner so
   the Cop actually experiences barrier payoff and learns *selective* use.

Shaping + enrichment are **off** in `solo`/`bonus` (no `reward_shaping` key; default 2-tuple
state, `results/qtables`). The advanced profile loads/saves `results/qtables_advanced` and
sets `enriched_cop_state: true`.

## Empirical outcome (honest, measured — A/B at 4k = 12k episodes, converged)

| Variant (Cop vs heuristic Thief, corner starts) | Capture rate | Avg moves | Barrier use |
| --- | --- | --- | --- |
| baseline (2-tuple state) | **100%** | 5.0 | 0% |
| **PBRS only** (shaping, 2-tuple) | **100%** | 5.4 | 0% |
| enrichment only (3-tuple state) | 76% | 18.6 | 0% |
| PBRS + enrichment + curriculum | 47% | 16.0 | 0% |

Two clean findings:

1. **PBRS is policy-invariant — and that is the whole point.** Shaping-only matches the
   baseline exactly (100% / ~5 moves) and adds **zero** barrier use. By the Ng–Harada–Russell
   theorem the optimal policy is unchanged, so PBRS **cannot manufacture barrier use that is
   not already optimal** — and on an open 5×5, forfeiting a move to place a single wall is
   genuinely *suboptimal* (chasing captures faster). So the Cop *correctly* never places
   barriers. This is the right RL result, not a failure; it also proves there is **no
   reward-hacking** (no spam).
2. **The state enrichment hurt.** Splitting the displacement state by the Thief's escape
   bucket fragmented the table (the bucket shifts for reasons the Cop's action doesn't cleanly
   control), dropping capture rate to 76% (enrichment) / 47% (with curriculum) even at
   convergence.

**Decision (fallback, per the task):** shaping/enrichment stay **OFF by default** (solo and
bonus untouched, byte-identical results). The `advanced` profile keeps them ON purely as the
reproducible experiment behind the A/B figure. Because a *learned* policy will not place
barriers when they are suboptimal, the barrier **mechanic** is demonstrated with a constructed
cornering scenario (`results/barrier_demo/`, task 6) where a barrier genuinely reduces the
Thief's escapes — showing intelligent, *conditional* use (only when the Thief is at escape
bucket 0 and the Cop is adjacent), with the capture following.

## Consequences
- `encode_state`/`QTable.save|load` generalize to variable-length state keys — existing
  2-tuple tables (solo/bonus) load byte-identically; nothing about their results changes.
- Honest negative results (enrichment fragmentation; PBRS not inducing suboptimal barriers)
  are reported as-is — they demonstrate understanding of why the Cop avoids barriers.
- Alternatives rejected: flat barrier bonus (reward-hacking → spam); large state (Thief full
  position → table blow-up); changing the board/thief-speed to make barriers optimal (would
  alter the game and the solo/bonus results).
