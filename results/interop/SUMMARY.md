# Bonus Inter-Team Match — SUMMARY

**il-nv-ai ↔️ vm__fabi · peer-to-peer cop-robber over MCP**

| | |
| --- | --- |
| **Match date** | 2026-06-26 (Asia/Jerusalem) |
| **Group 1 (Team A)** | **il-nv-ai** — Ilya Lazarev (212177943), Nadav Goldin (316350768) |
| **Group 2 (Team B)** | **vm__fabi** — Vasily Mironovich (345606545), Fahed Bitar (211758149) |
| **Group 1 repo** | https://github.com/ilyalaz01/robocopMCP |
| **Group 2 repo** | https://github.com/mironovich-v/cop-rob |
| **Team B MCP server** | https://cop-rob-player-agent-78e1.onrender.com/mcp (FastMCP streamable-http) |
| **Ruleset** | `cop-robber-grid-v1` · hash `a0df8e78a545501805496d36110fa6e2850d073d72639632a3abac354fc35140` |
| **Seed protocol** | `commit_reveal` (both nonces → per-sub-game seed → deterministic starts) |

## Final result — **DRAW, 75–75**

| Group | Total score | Bonus claim |
| --- | --- | --- |
| il-nv-ai | **75** | **5** |
| vm__fabi | **75** | **5** |

A tie awards the bonus 5/5 to each team (opponent assignment §19.3).

### Agreed canonical report hash

```
393b81f31a258c7832d6a149085820f75d0f1458a99026142eab0304f62941e2
```

This is `SHA-256` of the canonical JSON of `report_bonus.json` **excluding the
`mutual_agreement` flag** (the flag is the *result* of agreeing, so it cannot be
part of the agreed-on hash). Both teams computed the same hash → `mutual_agreement = true`.
Reproduce:

```bash
python -c "import json,hashlib; r=json.load(open('report_bonus.json')); \
r={k:v for k,v in r.items() if k!='mutual_agreement'}; \
print(hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':')).encode()).hexdigest())"
# -> 393b81f31a258c7832d6a149085820f75d0f1458a99026142eab0304f62941e2
```

### Email report message IDs (Gmail)

Both teams emailed the agreed JSON report to `rmisegal+uoh26b@gmail.com`:

| Sender | Gmail message_id |
| --- | --- |
| il-nv-ai (ours) | `19f015becb6345fb` |
| vm__fabi (theirs) | `19f015dc2970c0e8` |

## Role schedule & the 6 sub-games

Deterministic team-name ordering (trim/lowercase/lexicographic): `il-nv-ai < vm__fabi`
→ **il-nv-ai = Team A**, **vm__fabi = Team B**. Schedule: A=Cop in sub-games 1–3,
A=Robber in sub-games 4–6 (Robber moves first each ply).

| SG | il-nv-ai role | vm__fabi role | terminal_reason | winner | cop / robber score | log_hash (first 12) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Cop | Robber | cop_capture | cop | 20 / 5 | `d9c653a3190d` |
| 2 | Cop | Robber | cop_capture | cop | 20 / 5 | `18e9282dbd29` |
| 3 | Cop | Robber | cop_capture | cop | 20 / 5 | `48aa321f3df0` |
| 4 | Robber | Cop | cop_capture | cop | 20 / 5 | `579529dd4065` |
| 5 | Robber | Cop | cop_capture | cop | 20 / 5 | `ccc03d056eb6` |
| 6 | Robber | Cop | cop_capture | cop | 20 / 5 | `7d507810ae8b` |

Both sides' cop policy captured on the open 5×5 board in every sub-game, so each team
won the three sub-games in which it played Cop → **60 + 15 = 75 each**. Per-ply detail
and the exchange protocol are in `SUBGAMES.md` and `HANDSHAKE_LOG.md`.

## Files in this folder

- `report_bonus.json` — the final agreed bonus report (schema = assignment §18.6; `mutual_agreement=true`).
- `email_body.txt` — the JSON body emailed to the grader (identical content to the report).
- `SUBGAMES.md` — per-sub-game outcomes (roles, terminal reason, winner, scores, log hash).
- `HANDSHAKE_LOG.md` — the full pre-game + result-exchange protocol with the confirmed bit-exact values.
- `INTEROP_SUMMARY.md` — technical history: the key interop decisions and fixes.
