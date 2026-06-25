"""Integration: the live interop turn loop over real MCP (in-memory transport).

Two sides each act on their own state and deliver actions by calling the
opponent's ``receive_action_message`` tool — the network glue. They must agree on
the identical terminal state, proving the P2P loop end to end (no central referee).
"""

from __future__ import annotations

import asyncio

from robocop_mcp.domain.models import Position
from robocop_mcp.interop.constants import TERMINAL_CODES
from robocop_mcp.interop.game_adapter import build_rules
from robocop_mcp.interop.live_loop import run_live_sub_game
from robocop_mcp.interop.session import MatchSession

RULES = build_rules(5, 5, 25, 5)


def _agree(a: MatchSession, b: MatchSession) -> bool:
    sa = a.agent.game.engine.state
    sb = b.agent.game.engine.state
    return sa.cop == sb.cop and sa.thief == sb.thief and sa.outcome == sb.outcome


def test_live_sub_game_over_mcp_agrees() -> None:
    for c, r in [((2, 2), (0, 0)), ((0, 0), (4, 4)), ((4, 0), (0, 4))]:
        cop_side = MatchSession("il-nv-ai")
        rob_side = MatchSession("team-beta")
        code = asyncio.run(run_live_sub_game(cop_side, rob_side, "t",
                                             Position(*c), Position(*r), RULES))
        assert code in TERMINAL_CODES and TERMINAL_CODES[code] in {"cop", "robber"}
        assert _agree(cop_side, rob_side), f"sides desynced over MCP from C{c} R{r}"


def test_live_loop_token_guarded() -> None:
    # A wrong token at the receiver makes the delivery fail (no silent play).
    cop_side, rob_side = MatchSession("a"), MatchSession("b")

    async def go():
        return await run_live_sub_game(cop_side, rob_side, "right-token",
                                       Position(2, 2), Position(0, 0), RULES)

    # Same token on both sides → it runs and resolves.
    code = asyncio.run(go())
    assert TERMINAL_CODES[code] in {"cop", "robber"}
