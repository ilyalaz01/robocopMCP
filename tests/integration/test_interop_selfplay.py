"""Integration: two interop PlayerAgents play a full P2P sub-game (mocked LLM).

The highest-value proof: with NO central referee, each agent maintains its own
inferred state, exchanges natural-language action messages, and they agree on the
identical terminal state — validating the protocol + translation without a live
opponent.
"""

from __future__ import annotations

from robocop_mcp.domain.models import Position
from robocop_mcp.interop.constants import TERMINAL_CODES
from robocop_mcp.interop.game_adapter import build_rules
from robocop_mcp.interop.peer_agent import PlayerAgent, play_sub_game
from robocop_mcp.interop.translation import OpponentProfile, Translator

RULES = build_rules(5, 5, 25, 5)


def _agree(a: PlayerAgent, b: PlayerAgent) -> bool:
    sa, sb = a.game.engine.state, b.game.engine.state
    return (sa.cop == sb.cop and sa.thief == sb.thief
            and sa.outcome == sb.outcome and sa.barriers == sb.barriers)


def test_full_sub_game_agrees_on_result() -> None:
    cop, rob = PlayerAgent("il-nv-ai"), PlayerAgent("team-beta")
    for c, r in [((2, 2), (0, 0)), ((0, 0), (4, 4)), ((2, 0), (2, 4))]:
        code = play_sub_game(cop, rob, Position(*c), Position(*r), RULES)
        assert code in TERMINAL_CODES and TERMINAL_CODES[code] in {"cop", "robber"}
        assert _agree(cop, rob), f"agents desynced from C{c} R{r}"


def test_both_agents_log_the_exchange() -> None:
    cop, rob = PlayerAgent("il-nv-ai"), PlayerAgent("team-beta")
    play_sub_game(cop, rob, Position(2, 2), Position(0, 0), RULES)
    # Each agent recorded both its own and the opponent's actions.
    assert any(e.get("observed") for e in cop.log)
    assert len(cop.log) == len(rob.log) >= 2


def test_self_play_with_custom_opponent_profile() -> None:
    # Adaptation proof: a non-default direction phrasing still drives a clean game.
    profile = OpponentProfile(move_template="I shift {word}.")
    t = Translator(profile)
    cop, rob = PlayerAgent("aaa", translator=t), PlayerAgent("bbb", translator=t)
    code = play_sub_game(cop, rob, Position(1, 1), Position(3, 3), RULES)
    assert TERMINAL_CODES[code] in {"cop", "robber"}
    assert _agree(cop, rob)
