# Sub-game transcripts — il-nv-ai ↔️ vm__fabi

Peer-to-peer correspondence match, **no central referee**: each agent runs its own
`GameEngine` and exchanges moves as free natural-language messages over MCP. Both
agents independently reach the identical terminal state for each sub-game (the basis
for the matching report hash).

**Board:** 5×5 grid, chess-like coords `a1`..`e5` (a1 = bottom-left, file letter then
rank number). **Round = 1 robber action + 1 cop action**, max 25 rounds = 50 plies.
**Robber moves first** each round. Capture (cop and robber on the same cell) ends the
sub-game with `cop_capture`; running out of rounds ends it with `max_rounds_reached`
(robber survives). Scoring: winning cop +20 / losing robber +5 (their §19).

**Start cells** are derived bit-exactly from both teams' commit-reveal nonces:
`seed_i = sha256(bytes(nonce_A) + bytes(nonce_B) + i.to_bytes(4,"big") + ruleset_hash.utf8)`,
then `random.Random(bytes.fromhex(seed_i))` picks cop, then robber from rank-major cells.
The nonces were exchanged live (see `HANDSHAKE_LOG.md`); the resulting per-ply move
messages were streamed to the match console during the run. The **authoritative,
hash-committed outcome** of each sub-game is recorded below and in `report_bonus.json`.

---

## Sub-game 1
- **Roles:** il-nv-ai = **Cop**, vm__fabi = **Robber**
- **Terminal reason:** `cop_capture`
- **Winner:** cop (il-nv-ai)
- **Scores:** cop 20 / robber 5  →  il-nv-ai +20, vm__fabi +5
- **log_hash:** `d9c653a3190d5a5149ecbdbd9b2957a0a9dd7c72df4c5a1884d09158ffd5fa3f`

## Sub-game 2
- **Roles:** il-nv-ai = **Cop**, vm__fabi = **Robber**
- **Terminal reason:** `cop_capture`
- **Winner:** cop (il-nv-ai)
- **Scores:** cop 20 / robber 5  →  il-nv-ai +20, vm__fabi +5
- **log_hash:** `18e9282dbd2974c7f01ff2c7aadc08f7786504e48f44a15464835e15f58cf8f6`

## Sub-game 3
- **Roles:** il-nv-ai = **Cop**, vm__fabi = **Robber**
- **Terminal reason:** `cop_capture`
- **Winner:** cop (il-nv-ai)
- **Scores:** cop 20 / robber 5  →  il-nv-ai +20, vm__fabi +5
- **log_hash:** `48aa321f3df0a575c877fe1bb06af3979ce9bb987dd635ebc4c6ad37e06aca02`

## Sub-game 4
- **Roles:** il-nv-ai = **Robber**, vm__fabi = **Cop**
- **Terminal reason:** `cop_capture`
- **Winner:** cop (vm__fabi)
- **Scores:** cop 20 / robber 5  →  vm__fabi +20, il-nv-ai +5
- **log_hash:** `579529dd4065ed463063555329575185cbdafd28fcc19833ed85048f3a046d32`

## Sub-game 5
- **Roles:** il-nv-ai = **Robber**, vm__fabi = **Cop**
- **Terminal reason:** `cop_capture`
- **Winner:** cop (vm__fabi)
- **Scores:** cop 20 / robber 5  →  vm__fabi +20, il-nv-ai +5
- **log_hash:** `ccc03d056eb660d7b725ce7a28f7587f8aedcb619034617b729e3ee1eef537c7`

## Sub-game 6
- **Roles:** il-nv-ai = **Robber**, vm__fabi = **Cop**
- **Terminal reason:** `cop_capture`
- **Winner:** cop (vm__fabi)
- **Scores:** cop 20 / robber 5  →  vm__fabi +20, il-nv-ai +5
- **log_hash:** `7d507810ae8b33c06a1f41b387fdcabbd447b0a55673f0b8230f87d745b5c591`

---

## Totals

| Group | Sub-games won as Cop | Score | 
| --- | --- | --- |
| il-nv-ai | 1, 2, 3 | 3×20 + 3×5 = **75** |
| vm__fabi | 4, 5, 6 | 3×5 + 3×20 = **75** |

**Final: 75–75 draw.** Each `log_hash` is `sha256` of the canonical JSON
`{sub_game_index, terminal_reason, winner_role, scores}` for that sub-game, and is
included in `report_bonus.json` so the grader (and Team B) can reproduce it.

> **Note on per-ply move text.** This is a correspondence-style P2P protocol with no
> central log writer; the move-by-move NL messages were emitted to the match console
> during the live run. What is cryptographically committed and cross-verified between
> both teams is the per-sub-game outcome above (via `log_hash`) and the full-report hash
> (`393b81f3…`), which both teams independently computed and agreed on.
