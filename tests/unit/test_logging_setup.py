"""Tests for structured logging — JSONL event stream (Phase 0)."""

from __future__ import annotations

import json

from robocop_mcp.shared.config import ConfigManager
from robocop_mcp.shared.logging_setup import get_logger, log_event, setup_logging


def test_setup_returns_jsonl_path(temp_config: ConfigManager) -> None:
    path = setup_logging(temp_config)
    assert path.name == "events.jsonl"
    assert path.parent.is_dir()


def test_log_event_appends_jsonl(tmp_path) -> None:
    jsonl = tmp_path / "events.jsonl"
    rec = log_event(jsonl, "turn", role="cop", move="N", step=3)
    assert rec["event"] == "turn"
    assert rec["role"] == "cop"
    lines = jsonl.read_text().strip().splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["event"] == "turn"
    assert parsed["step"] == 3
    assert "ts" in parsed and "mono" in parsed


def test_log_event_multiple_lines(tmp_path) -> None:
    jsonl = tmp_path / "events.jsonl"
    for i in range(5):
        log_event(jsonl, "move", step=i)
    assert len(jsonl.read_text().strip().splitlines()) == 5


def test_get_logger_namespaced() -> None:
    assert get_logger("robocop.test").name == "robocop.test"
