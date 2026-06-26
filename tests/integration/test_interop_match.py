"""Integration: the bidirectional match runner vs a simulated opponent (no net).

The simulator stands in for the remote server: it applies our outbound moves to
its mirror and, on its turns, feeds its own moves into our shared session (as our
in-process server would when the real opponent calls us). Validates the full
6-sub-game driver + dry-run finalize without a live opponent.
"""

from __future__ import annotations

import asyncio

from robocop_mcp.domain.models import Position
from robocop_mcp.interop.game_adapter import ROLE_FROM_STR, InteropGame
from robocop_mcp.interop.match_runner import run_match
from robocop_mcp.interop.peer_agent import default_policy
from robocop_mcp.interop.session import MatchSession
from robocop_mcp.interop.translation import Translator

MATCH_INFO = {"their_repo": "gh-b", "their_cop_url": "c", "their_thief_url": "t",
              "their_students": []}
T = Translator()


def _make_sim(session: MatchSession):
    """Return (their_client_stub, await_opponent) backed by a mirror game."""
    rules = session.rules
    st: dict = {"mirror": None, "role": None}

    def _apply(game, role, message):
        p = T.parse_action(message)
        if p["type"] == "move":
            game.apply_move(role, p["direction"])
        elif p["type"] == "block":
            game.apply_block(role)
        else:
            game.admit_loss(role)

    class Their:
        async def start_sub_game(self, index, role, cop_pos, robber_pos, **kw):
            st["role"] = ROLE_FROM_STR[role]
            g = InteropGame(rules)
            g.start(Position(*T.coord_to_cell(cop_pos)), Position(*T.coord_to_cell(robber_pos)))
            st["mirror"] = g
            return {"status": "ok"}

        async def receive_action_message(self, index, rnd, actor, message):
            _apply(st["mirror"], ROLE_FROM_STR[actor], message)  # our move on their mirror
            return {"status": "ok"}

    async def await_opponent(_our_game, _timeout):
        g, role = st["mirror"], st["role"]
        if g.engine.state.is_terminal():
            return True
        if not g.has_legal_action(role):
            msg = T.phrase_loss()
        else:
            kind, direction = default_policy(g, role)
            msg = T.phrase_move(direction) if kind == "move" else (
                T.phrase_block() if kind == "block" else T.phrase_loss())
        _apply(g, role, msg)                    # advance their mirror
        session.agent.observe(msg, role)        # feed their move into OUR shared game
        return True

    return Their(), await_opponent


def test_run_match_against_simulated_opponent(tmp_path) -> None:
    session = MatchSession("il-nv-ai")
    session.set_opponent("vm__fabi")
    their, await_opp = _make_sim(session)
    starts = [(Position(0, 0), Position(4, 4))] * 6
    res = asyncio.run(run_match(session, their, starts, await_opp, MATCH_INFO, tmp_path))

    assert len(session.results) == 6
    assert (tmp_path / "report_bonus.json").is_file()
    assert res["status"] == "dry_run" and res["sent"] is False  # NEVER auto-send
    assert len(res["hash"]) == 64  # raw SHA-256 hex, no prefix
