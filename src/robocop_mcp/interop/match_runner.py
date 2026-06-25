"""Bidirectional match driver — plays 6 sub-games against a remote opponent.

On OUR turn the runner picks a legal action, applies it to our own state, and
delivers it by calling the opponent's ``receive_action_message``. On THEIR turn
it awaits their move arriving at our in-process server (which updates the shared
session) via the injected ``await_opponent`` coroutine — so the loop is testable
without a live opponent. After 6 sub-games it finalizes a DRY-RUN bonus report
(saves report_bonus.json, prints SHA256, never emails).
"""

from __future__ import annotations

from pathlib import Path

from ..constants import Role
from ..domain.models import Position
from .capability_handshake import role_for
from .constants import TERMINAL_CODES
from .finalize import finalize
from .game_adapter import STR_FROM_ROLE
from .session import MatchSession


def _coord(p: Position) -> str:
    return f"{chr(97 + p.x)}{p.y + 1}"


async def run_sub_game(session: MatchSession, their, index: int, role: Role,
                       cop: Position, robber: Position, await_opponent, timeout: float = 60.0):
    """Play one sub-game to a terminal code; our turns call the opponent."""
    session.agent.start_sub_game(role, cop, robber, session.rules)
    their_role = Role.THIEF if role is Role.COP else Role.COP
    await their.start_sub_game(index, STR_FROM_ROLE[their_role], _coord(cop), _coord(robber))

    game = session.agent.game
    code = None
    for ply in range(session.rules.max_moves + 2):
        if game.engine.state.is_terminal():
            break
        if game.engine.state.turn is role:  # our turn → decide + deliver to them
            if not game.has_legal_action(role):
                code = game.no_legal_action_code(role)
                await their.receive_action_message(index, ply, STR_FROM_ROLE[role],
                                                   session.agent.translator.phrase_loss())
                break
            message, code = session.agent.act()
            await their.receive_action_message(index, ply, STR_FROM_ROLE[role], message)
        else:  # their turn → wait for their call to our server (updates the shared game)
            if not await await_opponent(game, timeout):
                code = f"{STR_FROM_ROLE[their_role]}_timeout_retry_failed"
                break
            code = game.terminal_code
        if code:
            break

    winner = TERMINAL_CODES.get(code)
    cop_s, rob_s = (20, 5) if winner == "cop" else (5, 10)
    session.sub_game_result(index, code, winner, cop_s, rob_s)
    return code


async def run_match(session: MatchSession, their, starts: list, await_opponent,
                    match_info: dict, out_dir: Path, num_games: int = 6) -> dict:
    """Play ``num_games`` sub-games (role schedule) then finalize a dry-run report."""
    for index in range(1, num_games + 1):
        role = role_for(index, session.our_team, session.team_a)
        cop, robber = starts[index - 1]
        await run_sub_game(session, their, index, role, cop, robber, await_opponent)

    # NEVER auto-send: dry-run only — saves report_bonus.json + prints SHA256.
    result = finalize(session, match_info, out_dir, send=False)
    print("MATCH DONE. report_bonus.json SHA256:", result["hash"], "| sent:", result["sent"])
    return result
