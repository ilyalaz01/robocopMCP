"""Tests for the natural-language layer with a fully mocked LLM (no network)."""

from __future__ import annotations

import pytest

from robocop_mcp.agents.language import LanguageEngine, _extract_text
from robocop_mcp.constants import Role
from robocop_mcp.shared.gatekeeper import ApiGatekeeper


class _Block:
    def __init__(self, text: str) -> None:
        self.text = text


class _Resp:
    def __init__(self, text: str) -> None:
        self.content = [_Block(text)]


def _gatekeeper(tmp_path):
    limits = {"requests_per_minute": 100, "requests_per_hour": 1000,
              "retry_after_seconds": 0, "max_retries": 1, "max_queue_depth": 10}
    return ApiGatekeeper(limits, service="anthropic", jsonl=tmp_path / "e.jsonl")


def _engine(tmp_path, create_fn):
    return LanguageEngine(_gatekeeper(tmp_path), create_fn, "m", 256, 0.7, 5,
                          jsonl=tmp_path / "e.jsonl")


def test_message_uses_llm(tmp_path) -> None:
    def create(**kw):
        return _Resp("You'll never catch me, copper!")

    eng = _engine(tmp_path, create)
    msg = eng.message(Role.THIEF, {"move_count": 3, "opponent_pos": None}, [], "NE")
    assert msg == "You'll never catch me, copper!"


def test_message_passes_context(tmp_path) -> None:
    seen = {}

    def create(**kw):
        seen["user"] = kw["messages"][0]["content"]
        seen["system"] = kw["system"]
        return _Resp("ok")

    eng = _engine(tmp_path, create)
    eng.message(Role.COP, {"move_count": 7, "opponent_pos": [2, 2]}, [{"text": "hi"}], "E")
    assert "COP" in seen["system"]
    assert "Turn 7" in seen["user"] and 'last words: "hi"' in seen["user"]


def test_message_fallback_on_error(tmp_path) -> None:
    def boom(**kw):
        raise RuntimeError("api down")

    eng = _engine(tmp_path, boom)
    msg = eng.message(Role.COP, {"move_count": 1}, [], "N")
    assert "cop" in msg and "closing in" in msg
    assert "llm_fallback" in (tmp_path / "e.jsonl").read_text()


def test_interpret_returns_token(tmp_path) -> None:
    eng = _engine(tmp_path, lambda **kw: _Resp("  north \n"))
    assert eng.interpret(Role.COP, "I'm up top") == "NORTH"


def test_interpret_fallback_unknown(tmp_path) -> None:
    def boom(**kw):
        raise RuntimeError("x")

    assert _engine(tmp_path, boom).interpret(Role.COP, "msg") == "UNKNOWN"


def test_extract_text_plain_string() -> None:
    assert _extract_text("hello") == "hello"


def test_negotiation_line_uses_negotiator_persona(tmp_path) -> None:
    captured = {}

    def create(**kw):
        captured["system"] = kw["system"]
        return _Resp("How about we allow seven barriers?")

    eng = _engine(tmp_path, create)
    line = eng.negotiation_line(Role.COP, "propose", "max_barriers=7")
    assert line == "How about we allow seven barriers?"
    assert "negotiat" in captured["system"].lower()


def test_negotiation_line_fallback(tmp_path) -> None:
    def boom(**kw):
        raise RuntimeError("down")

    line = _engine(tmp_path, boom).negotiation_line(Role.THIEF, "accept", "ok")
    assert line == "[thief] accept: ok"


@pytest.mark.parametrize("role", [Role.COP, Role.THIEF])
def test_persona_distinct(tmp_path, role) -> None:
    captured = {}

    def create(**kw):
        captured["system"] = kw["system"]
        return _Resp("msg")

    _engine(tmp_path, create).message(role, {"move_count": 0}, [], None)
    assert role.value.upper() in captured["system"]


def test_deception_true_uses_bluff_persona(tmp_path) -> None:
    captured = {}

    def create(**kw):
        captured["system"] = kw["system"]
        return _Resp("msg")

    eng = _engine(tmp_path, create)
    eng.deception = True
    eng.message(Role.THIEF, {"move_count": 0}, [], None)
    assert "bluff" in captured["system"].lower()


def test_deception_false_uses_truthful_persona(tmp_path) -> None:
    captured = {}

    def create(**kw):
        captured["system"] = kw["system"]
        return _Resp("msg")

    eng = _engine(tmp_path, create)
    eng.deception = False
    eng.message(Role.THIEF, {"move_count": 0}, [], None)
    system = captured["system"].lower()
    assert "truthful" in system and "never" in system  # must not lie about position/intent
