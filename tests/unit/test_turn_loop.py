"""Unit tests for the default heuristic decider."""

from __future__ import annotations

from robocop_mcp.constants import Role
from robocop_mcp.orchestrator.turn_loop import (
    _action_from_suggestion,
    default_decider,
    make_llm_decider,
)


class _FakeLang:
    def __init__(self) -> None:
        self.interpreted: list[str] = []

    def message(self, role, obs, msgs, sug) -> str:
        return f"msg-{role.value}-{sug}"

    def interpret(self, role, text) -> str:
        self.interpreted.append(text)
        return "NORTH"


def test_decider_follows_suggestion() -> None:
    msg, (kind, direction) = default_decider(Role.COP, {"move_count": 2}, [], "NE")
    assert kind == "move" and direction == "NE"
    assert "moving NE" in msg


def test_decider_cop_boxed_places_barrier() -> None:
    _, (kind, direction) = default_decider(Role.COP, {"move_count": 5}, [], None)
    assert kind == "barrier" and direction is None


def test_decider_barrier_suggestion() -> None:
    _, (kind, direction) = default_decider(Role.COP, {"move_count": 3}, [], "PLACE_BARRIER")
    assert kind == "barrier" and direction is None


def test_decider_thief_cornered() -> None:
    msg, (kind, direction) = default_decider(Role.THIEF, {"move_count": 9}, [], None)
    assert kind == "move" and direction is None
    assert "cornered" in msg


def test_action_from_suggestion_mapping() -> None:
    assert _action_from_suggestion(Role.COP, "PLACE_BARRIER") == ("barrier", None)
    assert _action_from_suggestion(Role.COP, None) == ("barrier", None)
    assert _action_from_suggestion(Role.THIEF, None) == ("move", None)
    assert _action_from_suggestion(Role.THIEF, "W") == ("move", "W")


def test_llm_decider_message_and_belief(tmp_path) -> None:
    lang = _FakeLang()
    jsonl = tmp_path / "e.jsonl"
    decide = make_llm_decider(lang, jsonl)
    msg, action = decide(Role.COP, {"move_count": 1}, [{"text": "catch me"}], "NE")
    assert msg == "msg-cop-NE" and action == ("move", "NE")
    assert lang.interpreted == ["catch me"]
    assert "belief" in jsonl.read_text()


def test_llm_decider_no_messages_skips_interpret(tmp_path) -> None:
    lang = _FakeLang()
    decide = make_llm_decider(lang, tmp_path / "e.jsonl")
    _, action = decide(Role.THIEF, {"move_count": 0}, [], None)
    assert action == ("move", None)
    assert lang.interpreted == []
