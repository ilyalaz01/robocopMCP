# Inter-team Bonus Match — Agreed Rules

**Teams:** `il-nv-ai` (Ilya Lazarev, Nadav Goldin) ↔ `[TEAM 2 CODE / NAMES]`
**Course:** Prof. Yoram Segal, EX06 bonus · **Report recipient:** rmisegal+uoh26b@gmail.com

> Both teams load this document into their agents as the binding ruleset, and configure their
> engines to match it exactly. The agents talk in free natural language over MCP, but must
> follow these rules.

## Fixed rules (identical for both teams — do not change)
- Grid: **5 × 5**.
- Sub-game: **max 25 moves**; **Thief moves first**, then Cop; repeat.
- Movement: **one step in any of the 8 directions** (including diagonal).
- **Cop wins** by landing on the **exact** cell of the Thief (capture).
- **Thief wins** by surviving the full 25 moves uncaught.
- **Barriers:** the **Cop** may place a barrier on its own cell instead of moving (this
  forfeits the Cop's move that turn); that cell becomes **impassable to the Thief**; the Thief
  cannot place barriers.
- **Scoring per sub-game:** Cop catches → Cop **20**, Thief **5**; Thief escapes → Cop **5**,
  Thief **10**.
- **Series = 6 sub-games.** Role split: **sub-games 1–3** = Team A Cop vs Team B Thief;
  **sub-games 4–6** = Team B Cop vs Team A Thief.

## The two key agreements (the important part)
- **Open information** — both agents always know the **exact, full board state** (both
  positions + all barriers) from the start of every sub-game.
- **No deception / no lying** — every message must be **truthful**; no bluffing about position
  or intent.

> Why: in a peer-to-peer match with no trusted referee, open + truthful play is the only clean
> way for both teams to compute and report the **identical** result. (Hidden state + lying
> would need a trusted host or cryptographic commit-reveal / ZKP.)

## Fixed starting positions (both teams hardcode these — guarantees identical games)
| Sub-game | Cop start | Thief start |
| --- | --- | --- |
| 1 | (0, 0) | (4, 4) |
| 2 | (4, 0) | (0, 4) |
| 3 | (2, 0) | (2, 4) |
| 4 | (0, 4) | (4, 0) |
| 5 | (4, 4) | (0, 0) |
| 6 | (0, 2) | (4, 2) |

## Negotiable (for the dialogue only — converge on these exact values)
The agents hold a short natural-language negotiation and **converge on**:
- `max_barriers` = **5** (they may briefly discuss within 3–8, then settle on **5**).
- `max_moves` = **25**.

Everything else is fixed. The negotiation is real but brief; its agreed outcome must equal the
values above so both engines stay identical.

## Coordinator / hosting
Either team may host the match. The agents settle leadership during the negotiation (our agent
proposes to host but yields gracefully if yours insists). **The hosting team's orchestrator
produces the official bonus-report JSON** (exact schema) and shares it with the other team.

## Result reporting (mismatch = bonus 0 for BOTH teams)
**Both teams email the byte-identical bonus JSON** (the host's output) to
**rmisegal+uoh26b@gmail.com**, each from their own account. The email body contains **only**
the JSON (no free text). Set `mutual_agreement: true`.

## Exchange checklist (fill in before the match)
| Item | Team A — `il-nv-ai` | Team B — `[code]` |
| --- | --- | --- |
| GitHub repo | https://github.com/ilyalaz01/robocopMCP | `[ ]` |
| Cop MCP URL | `[ after deploy ]` | `[ ]` |
| Thief MCP URL | `[ after deploy ]` | `[ ]` |
| Server token (revocable) | `[ from our config/.env ]` | `[ ]` |
| Students (name + ID) | Ilya Lazarev 212177943; Nadav Goldin 316350768 | `[ ]` |
