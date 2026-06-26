# Cost & Token Analysis (rubric §10)

**Model:** `claude-haiku-4-5-20251001` (Anthropic) for all natural-language generation
and interpretation. **Pricing used:** Haiku list rate **$1.00 / 1M input tokens**,
**$5.00 / 1M output tokens** (`src/robocop_mcp/reporting/summary.py:HAIKU_RATES`).

All token counts are measured, not estimated: the API Gatekeeper records
`input_tokens` / `output_tokens` on **every** call
(`shared/gatekeeper.py` → `_usage()` → `api_call` event), and each run's
`results/<run>/summary.json` aggregates them via `reporting/summary.py:token_cost`.

## Summary table — all runs that used the LLM

| Run | Model | #Calls | Input tokens | Output tokens | Cost (USD) | Source |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Solo series (6 sub-games, partial-obs, bluffing) | Haiku | 298 | 40,175 | 6,873 | **$0.074540** | `results/solo_demo/summary.json` |
| Host-bonus demo (truthful, full-vis, 6 sub-games) | Haiku | 386 | 51,967 | 8,756 | **$0.095747** | `results/bonus_demo/summary.json` |
| Inter-team bonus match vs vm__fabi | — (none) | 0 | 0 | 0 | **$0.000000** | see note below |
| **TOTAL** | | **684** | **92,142** | **15,629** | **$0.170287** | |

Cross-check: `92,142 / 1e6 × $1` + `15,629 / 1e6 × $5` = `$0.092142 + $0.078145` = **$0.170287**.

### Note — the inter-team bonus match used $0 in tokens

The P2P interop agent (`src/robocop_mcp/interop/`) phrases and parses moves with a
**deterministic translator** (`translation.py`, longest-match direction parsing), **not**
an LLM — it imports neither `anthropic` nor the gatekeeper. So the live match against
team **vm__fabi** made **zero** model calls and cost **$0**. This is an honest limitation:
**free natural-language-over-LLM communication is demonstrated in the solo run**
(`results/solo_demo/transcript.md`, with the Thief actively bluffing — e.g. "heading to
the docks" while moving elsewhere), where real Haiku both generates and interprets the
messages. The interop match satisfies the bonus protocol (commit-reveal, exact ruleset
hash, mutual report-hash agreement) but exchanges templated NL rather than LLM-authored NL.

## Per-turn economics

- Solo: 298 calls over 6 sub-games ≈ **~50 calls/sub-game** (message generation +
  interpretation + negotiation), averaging **~135 input / ~23 output tokens per call**.
- Messages are intentionally short (a single move intent + a brief observation), which is
  why output tokens are ~6× smaller than input tokens and the whole 6-game series costs
  **under 8 cents**.

## Optimization strategies (what the project actually does)

1. **Model choice — Haiku, not Opus/Sonnet.** Language + negotiation are short,
   low-reasoning tasks (describe a move, parse an opponent line). Haiku's list price is a
   fraction of Opus's; at 684 calls the whole project costs **$0.17** instead of dollars.
   Locked in config, not code (`config/config.json` → `llm.model`).
2. **Movement is deterministic, not LLM-driven.** The Q-table chooses *where* to move;
   the LLM only handles *language* (SPEC §5: "language and movement don't fight"). This
   removes an entire class of expensive reasoning calls — strategy costs $0 in tokens.
3. **Bounded interaction length.** `max_moves = 25` per sub-game and `num_games = 6` cap
   the number of turns (and therefore calls) deterministically, so cost can never run away
   (`config/config.json`). Negotiation also concedes after `max_rounds` — no infinite back-and-forth.
4. **Gatekeeper throttling + queue.** All calls pass through `ApiGatekeeper`
   (rate-limit → FIFO queue on overflow → bounded retries), preventing burst over-use and
   making spend observable (`config/rate_limits.json`, versioned).
5. **Templated fallback on timeout.** `LanguageEngine` falls back to a templated message if
   a call times out, so a stalled API call never triggers retries-to-infinity.
6. **Trimmed, regenerable logs.** Token accounting is summarized into `summary.json`; the
   raw `events.jsonl` committed for evidence is trimmed to keep the repo light.

## Budget projection at scale

At the measured rate (~$0.085 per 6-sub-game series with full Haiku NL), running, e.g.,
**100 inter-team series** with LLM phrasing enabled would cost roughly **$8.50** in tokens —
still negligible, confirming Haiku is the right cost/benefit choice for this workload.
