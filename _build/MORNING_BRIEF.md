# MORNING BRIEF — robocopMCP

**Date:** 2026-06-25 · **Group:** il-nv-ai

> **✅ UPDATE 2026-06-26 — INTER-TEAM BONUS MATCH COMPLETED.** The live P2P match vs
> **vm__fabi** has since been played to completion: **75–75 draw** (bonus 5/5 each), agreed
> canonical hash `393b81f31a258c7832d6a149085820f75d0f1458a99026142eab0304f62941e2`
> (`mutual_agreement=true`), both teams emailed the report (ours `19f015becb6345fb`, theirs
> `19f015dc2970c0e8`). The "Cloud deploy + run the bonus match" hand-off below is **DONE** —
> see `results/interop/` and `_build/INTEROP_STATUS.md` for full evidence. The text below
> records the pre-match state.

---

## TL;DR

**Phases 0–10 complete and pushed to GitHub.** A later session added the **inter-team bonus
profile** (open information + truthful messages) alongside the solo Dec-POMDP profile, and
fixed the "6 identical sub-games" defect with **varied per-sub-game starts**. Everything is
green. The only remaining work is the Phase 11 hand-offs that need the other team / external
accounts.

- **Tests:** 166 passed · **coverage ≥ 96%** · **ruff:** 0 errors · every code file ≤ 150 LOC.
- **No secrets committed** (`.env` + key file git-ignored; verified). Repo is on `main`.

## Two profiles (ADR-0003) — selected by `--profile` / `ROBOCOP_PROFILE`

| Profile | Visibility | Deception | Starts | Demo artifacts |
| --- | --- | --- | --- | --- |
| `solo` (default) | partial (`vision_radius=1`) | allowed (bluffing) | `seeded_random` (seed 42) | `results/solo_demo/` |
| `bonus` | **full** (open info) | **off** (truthful) | `fixed_pairs` (SHARED_RULES) | `results/bonus_demo/` |

## What works (verified)

| Capability | Evidence |
| --- | --- |
| Varied starts → 6 DIFFERENT sub-games | `results/solo_demo/summary.md` — 3 thief wins, 3 cop wins (moves 25/25/4/6/25/2) |
| Solo deception (bluffing) | `results/solo_demo/transcript.md` — Thief bluffs; Cop calls it a "misdirect" |
| Bonus truthful + full visibility | `results/bonus_demo/transcript.md` — Thief honestly says "off I go southbound" and does |
| Constrained negotiation (no invented rules) | `results/{solo,bonus}_demo/negotiation.md` — only barriers (3–8) + moves (25/30); bonus converges to 5/25 |
| Host-authoritative bonus design | `docs/adr/0002-state-sharing.md`; integration test `tests/integration/test_bonus_pipeline.py` |
| Exact-schema bonus report | `sdk.build_bonus_report(...)` (mutual_agreement set) |
| Research notebook + graphs + cost | `notebooks/analysis.ipynb` (executed, 0 errors); `assets/*.png` |

## What still needs YOU (Phase 11 — needs the other team / accounts)

1. **Confirm `_build/SHARED_RULES.md` with Team B** — fill in their group code, repo, MCP URLs,
   token, and students (the exchange checklist at the bottom). The 6 start pairs and converged
   values (max_barriers 5, max_moves 25) are already wired into `config/config_bonus.json`.
2. **Live Gmail OAuth send** — code-ready (`reporting/gmail_client.py`, mocked-tested). Needs
   `credentials.json` + browser consent → `token.json`, then `send_report(series, dry_run=False)`.
   Body is JSON only. Recipient `rmisegal+uoh26b@gmail.com` is in config.
3. **Cloud deploy + run the bonus match.** Expose both MCP servers publicly (ngrok/host) with
   the revocable token; exchange URLs with Team B. The **host** runs the bonus profile
   (`ROBOCOP_PROFILE=bonus`), calls its own agent locally + the remote agent over HTTP, and
   produces the bonus JSON; **both teams email the byte-identical body** with `mutual_agreement`.

## First 10 minutes when you wake up

```bash
uv run pytest                                   # 166 green
uv run robocop --play                           # solo series over MCP (no API cost) — now 6 varied games
ROBOCOP_PROFILE=bonus uv run robocop --play     # bonus profile (full visibility), fixed pairs
cat results/solo_demo/summary.md                # 3 thief / 3 cop wins (varied starts work)
open results/bonus_demo/transcript.md           # truthful, open-information play
open results/solo_demo/transcript.md            # deception / bluffing
open assets/sensitivity.png                     # headline research figure
```

## Decisions logged as ADRs

- **ADR-0001** — uv tooling, secret handling, in-place build.
- **ADR-0002** — in-process SessionRegistry locally; **host-authoritative** session for the bonus
  (open + truthful is why it's verifiable without a referee; partial+deception would need a
  trusted host or commit-reveal/ZKP).
- **ADR-0003** — solo vs bonus config profiles: visibility, deception, varied starts, constrained
  negotiation.

**Status: solo submission done + pushed; bonus profile code-complete and demonstrated locally.
Only the inter-team exchange + live send remain (need Team B / accounts).** 🚓💨
