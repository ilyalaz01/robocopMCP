"""Tests for the Markdown transcript builder (pure over logged events)."""

from __future__ import annotations

from robocop_mcp.reporting.transcript import render, write_transcript

EVENTS = [
    {"event": "subgame_start", "match_id": "m", "index": 0, "cop": [0, 0], "thief": [4, 4]},
    {"event": "turn", "session_id": "m-sg0", "role": "thief", "message": "catch me!",
     "direction": "S", "ok": True},
    {"event": "belief", "session_id": "m-sg0", "role": "cop", "belief": "SOUTH"},
    {"event": "turn", "session_id": "m-sg0", "role": "cop", "message": "closing in",
     "direction": "NE", "ok": True},
    {"event": "subgame_end", "match_id": "m", "index": 0, "outcome": "cop_win", "moves": 8,
     "cop_score": 20, "thief_score": 5},
    {"event": "series_end", "match_id": "m", "totals": {"cop": 20, "thief": 5}},
    {"event": "turn", "session_id": "other-sg0", "role": "cop", "message": "ignore me"},
]


def test_render_includes_messages_and_outcome() -> None:
    md = render(EVENTS, "m")
    assert "catch me!" in md and "closing in" in md
    assert "believes opponent is SOUTH" in md
    assert "cop_win in 8 moves" in md
    assert "Series totals" in md
    assert "ignore me" not in md  # belongs to a different match


def test_write_transcript(tmp_path) -> None:
    import json

    jsonl = tmp_path / "events.jsonl"
    jsonl.write_text("\n".join(json.dumps(e) for e in EVENTS))
    path = write_transcript(jsonl, "m", tmp_path / "results")
    assert path.is_file() and path.name == "transcript.md"
    assert "Sub-game 0" in path.read_text()
