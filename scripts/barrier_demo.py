"""Scripted barrier demonstration (ADR-0004, task 6).

On an open 5×5 with an equal-speed Cop and Thief-moves-first, walling is never the
*optimal* move (the Thief flees a corner before the Cop can wall, and whenever the
Cop is close enough to benefit it can simply capture) — so a *learned* policy never
places barriers (see the A/B in the notebook). This script therefore stages a clear
**constructed cornering scenario** over the real engine so the barrier MECHANIC and
its intelligent, conditional trigger are visible in the logs/transcript/PNGs: the
Cop walls one of a cornered Thief's escape routes (escape count drops 3→2) and the
capture follows two plies later.
"""

from __future__ import annotations

from robocop_mcp.constants import Direction, Role
from robocop_mcp.domain.engine import GameEngine
from robocop_mcp.domain.models import MatchRules, Position
from robocop_mcp.learning.shaping import thief_escape_count
from robocop_mcp.reporting.render import render_match
from robocop_mcp.reporting.transcript import write_transcript
from robocop_mcp.shared.config import ConfigManager
from robocop_mcp.shared.logging_setup import log_event, setup_logging

MATCH, SID = "barrier_demo", "barrier_demo-sg0"

# (role, kind, direction, message) — a deterministic cornering narrative.
SCRIPT = [
    (Role.THIEF, "move", "E", "Bolting east along the wall — catch me if you can!"),
    (Role.COP, "move", "SW", "Closing the gap from the north-east; you're drifting into the corner."),
    (Role.THIEF, "move", "W", "Back to my corner hideout — plenty of ways out from here."),
    (Role.COP, "barrier", None, "You're cornered with few exits — I'll wall off your north-east escape."),
    (Role.THIEF, "move", "N", "Fine, slipping north then!"),
    (Role.COP, "move", "W", "Right onto you — gotcha."),
]


def main() -> None:
    cfg = ConfigManager()
    jsonl = setup_logging(cfg)
    rules = MatchRules.from_config(cfg.game())
    engine = GameEngine(rules)
    engine.reset(cop=Position(2, 2), thief=Position(0, 0))
    log_event(jsonl, "subgame_start", match_id=MATCH, index=0,
              cop=engine.state.cop.as_tuple(), thief=engine.state.thief.as_tuple())
    log_event(jsonl, "state", session_id=SID, **engine._digest())

    for role, kind, direction, message in SCRIPT:
        escapes_before = thief_escape_count(engine)
        res = (engine.place_barrier(role) if kind == "barrier"
               else engine.apply_move(role, Direction(direction)))
        note = f" (thief escapes {escapes_before}->{thief_escape_count(engine)})"
        log_event(jsonl, "turn", session_id=SID, role=role.value, message=message + note,
                  action=kind, direction=direction, ok=res.ok, reason=res.reason)
        log_event(jsonl, "state", session_id=SID, **engine._digest())

    result = engine.result(index=0)
    log_event(jsonl, "subgame_end", match_id=MATCH, index=0, outcome=result.outcome.value,
              moves=result.moves, cop_score=result.cop_score, thief_score=result.thief_score)

    out = cfg.root / "results"
    write_transcript(jsonl, MATCH, out)
    render_match(jsonl, MATCH, 1, rules.grid_width, rules.grid_height, out)
    print(f"barrier demo: {result.outcome.value} in {result.moves} moves; "
          f"barriers placed at {sorted(b.as_tuple() for b in engine.state.barriers)}")
    print("artifacts in", out / MATCH)


if __name__ == "__main__":
    main()
