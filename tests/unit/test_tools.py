"""Tests for AgentToolService — token auth, observe, move, barrier, suggest."""

from __future__ import annotations

import pytest

from robocop_mcp.constants import Role
from robocop_mcp.domain.models import MatchRules, Position
from robocop_mcp.mcp.session import SessionRegistry
from robocop_mcp.mcp.tools import AgentToolService

TOKEN = "secret-token"


@pytest.fixture
def setup(base_game_config: dict, tmp_path):
    reg = SessionRegistry()
    rules = MatchRules.from_config(base_game_config)
    reg.create("m1", rules)
    jsonl = tmp_path / "events.jsonl"
    cop = AgentToolService(reg, Role.COP, TOKEN, jsonl)
    thief = AgentToolService(reg, Role.THIEF, TOKEN, jsonl)
    return reg, cop, thief, jsonl


def test_auth_rejects_bad_token(setup) -> None:
    _, cop, _, jsonl = setup
    res = cop.observe("m1", "wrong")
    assert not res["ok"] and "unauthorized" in res["error"]
    assert "auth_reject" in jsonl.read_text()


def test_no_session_error(setup) -> None:
    _, cop, _, _ = setup
    assert cop.observe("nope", TOKEN)["error"] == "no_session"


def test_observe_returns_partial(setup) -> None:
    _, cop, _, _ = setup
    obs = cop.observe("m1", TOKEN)["observation"]
    assert obs["self_pos"] == (0, 0)
    assert obs["role"] == "cop"
    assert obs["opponent_pos"] is None  # thief at (4,4) out of radius-1 view


def test_messaging_roundtrip(setup) -> None:
    _, cop, thief, _ = setup
    assert thief.send_message("m1", TOKEN, "you'll never catch me")["ok"]
    msgs = cop.read_messages("m1", TOKEN)["messages"]
    assert msgs[-1]["text"] == "you'll never catch me"


def test_move_legal_and_turn_order(setup) -> None:
    _, cop, thief, _ = setup
    # Cop cannot move first (thief's turn).
    assert "not_your_turn" in cop.move("m1", TOKEN, "N")["reason"]
    ok = thief.move("m1", TOKEN, "SW")
    assert ok["ok"] and ok["digest"]["thief"] == (3, 3)


def test_move_bad_direction(setup) -> None:
    _, _, thief, _ = setup
    assert "bad_direction" in thief.move("m1", TOKEN, "UP")["error"]


def test_illegal_move_rejected(setup) -> None:
    _, _, thief, _ = setup
    # Thief at (4,4) corner moving N (to (4,5)) is off-board.
    res = thief.move("m1", TOKEN, "N")
    assert not res["ok"] and "off_board" in res["reason"]


def test_suggest_move(setup) -> None:
    _, cop, _, _ = setup
    sug = cop.suggest_move("m1", TOKEN)
    assert sug["ok"] and sug["suggestion"] in {"N", "NE", "E"}  # toward (4,4) from (0,0)


def test_place_barrier_cop_only(setup) -> None:
    reg, cop, thief, _ = setup
    reg.get("m1").engine.reset(cop=Position(2, 2), thief=Position(4, 4))
    thief.move("m1", TOKEN, "SW")  # thief's turn first
    res = cop.place_barrier("m1", TOKEN)
    assert res["ok"] and res["digest"]["barriers"] == [(2, 2)]


def test_thief_barrier_forbidden(setup) -> None:
    _, _, thief, _ = setup
    res = thief.place_barrier("m1", TOKEN)
    assert not res["ok"] and "barrier_forbidden" in res["reason"]


def test_suggest_move_uses_qtable(base_game_config, tmp_path) -> None:
    import numpy as np

    from robocop_mcp.learning.q_learning import QTable, action_space, encode_state

    reg = SessionRegistry()
    reg.create("m1", MatchRules.from_config(base_game_config))
    acts = action_space(Role.COP)
    qt = QTable(acts, epsilon=0.0)
    # Cop at (0,0), unseen thief → target defaults to (4,4); state (4,4).
    row = np.zeros(len(acts))
    row[acts.index("NE")] = 9.0
    qt.q[encode_state(Position(0, 0), Position(4, 4))] = row
    cop = AgentToolService(reg, Role.COP, TOKEN, tmp_path / "e.jsonl", qtable=qt)
    assert cop.suggest_move("m1", TOKEN)["suggestion"] == "NE"


def test_enriched_suggest_places_barrier_when_cornering(base_game_config, tmp_path) -> None:
    import numpy as np

    from robocop_mcp.learning.q_learning import QTable, action_space
    from robocop_mcp.learning.shaping import cop_state

    reg = SessionRegistry()
    sess = reg.create("m1", MatchRules.from_config(base_game_config))
    sess.engine.reset(cop=Position(1, 0), thief=Position(0, 0))  # thief cornered, cop adjacent
    acts = action_space(Role.COP)
    qt = QTable(acts, epsilon=0.0)
    row = np.zeros(len(acts))
    row[acts.index("PLACE_BARRIER")] = 10.0
    qt.q[cop_state(sess.engine, enriched=True)] = row
    cop = AgentToolService(reg, Role.COP, TOKEN, tmp_path / "e.jsonl", qtable=qt, enrich=True)
    assert cop.suggest_move("m1", TOKEN)["suggestion"] == "PLACE_BARRIER"


def test_match_digest(setup) -> None:
    _, cop, _, _ = setup
    d = cop.match_digest("m1", TOKEN)["digest"]
    assert d["cop"] == (0, 0) and d["thief"] == (4, 4)


def test_auth_guards_all_tools(setup) -> None:
    _, cop, thief, _ = setup
    bad = "x"
    assert not cop.move("m1", bad, "N")["ok"]
    assert not cop.place_barrier("m1", bad)["ok"]
    assert not cop.suggest_move("m1", bad)["ok"]
    assert not cop.read_messages("m1", bad)["ok"]
    assert not cop.send_message("m1", bad, "hi")["ok"]
    assert not cop.match_digest("m1", bad)["ok"]
