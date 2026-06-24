# PRD — Game Engine (domain/)

**Version 1.00.** Authoritative, pure (no network/LLM), fully testable.

## Theoretical background
A discrete pursuit-evasion game on an `N×M` grid. Cop pursues, Thief evades, under partial
observability (Moore/Chebyshev `vision_radius`). The engine is the single source of truth;
MCP servers and orchestrator only *ask* it to validate and apply actions.

## Inputs / outputs / setup
- **Setup:** `grid_size`, `max_moves`, `max_barriers`, `vision_radius`, `scoring` (config).
- **Input:** an action — `Direction` move, or Cop `place_barrier`.
- **Output:** updated `GameState`, validation result, `Observation`, `SubGameResult`.

## Rules (authoritative)
1. Turn order **Thief → Cop**, repeating, up to `max_moves`.
2. Moves are one step in 8 directions (diagonal allowed); `STAY` only if rules permit;
   Thief may not be hard-coded to stand still.
3. Cop may **place a barrier** on its own cell instead of moving (forfeits the move); cell
   becomes impassable to the Thief; at most `max_barriers` per sub-game.
4. **Capture** = Cop occupies Thief's exact cell → `COP_WIN`. **Evasion** = Thief survives
   `max_moves` → `THIEF_WIN`.
5. **Illegal claims rejected:** off-board, >1 step, into a barrier, teleport.
6. **Scoring:** cop_win → Cop +20/Thief +5; thief_win → Cop +5/Thief +10. Series = 6 games.
7. **Void / technical loss:** a sub-game that errors out is void and re-run.

## Partial observation
Each agent sees cells within Chebyshev distance `vision_radius`; opponent visible only if
inside that window. Otherwise the orchestrator's belief (from language) supplies position.

## Edge cases (must be tested)
Capture on move 1; barrier on edge/occupied cell; barrier cap reached; max-moves timeout;
illegal move rejected; Thief blocked on all sides by barriers/edges; grid as small as 2×2.

## Success criteria
Deterministic given a seed; `domain/` coverage ≥ 90%; every rule above has a test.
