"""Tests for run-summary + token-cost accounting."""

from __future__ import annotations

import json

from robocop_mcp.constants import Outcome
from robocop_mcp.domain.models import SubGameResult
from robocop_mcp.orchestrator.orchestrator import SeriesResult
from robocop_mcp.reporting.summary import build_run_summary, summary_markdown, token_cost


def _jsonl(tmp_path, events):
    path = tmp_path / "events.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in events))
    return path


def test_token_cost_sums_and_prices(tmp_path) -> None:
    events = [
        {"event": "api_call", "input_tokens": 1_000_000, "output_tokens": 200_000},
        {"event": "api_call", "input_tokens": 0, "output_tokens": 0},
        {"event": "turn", "input_tokens": 999},  # ignored (not api_call)
    ]
    cost = token_cost(_jsonl(tmp_path, events))
    assert cost["api_calls"] == 2
    assert cost["input_tokens"] == 1_000_000 and cost["output_tokens"] == 200_000
    # 1M in * $1 + 0.2M out * $5 = $2.00
    assert cost["cost_usd"] == 2.0


def test_build_run_summary_and_markdown(tmp_path) -> None:
    series = SeriesResult("m", [
        SubGameResult(0, Outcome.COP_WIN, 8, 20, 5),
        SubGameResult(1, Outcome.THIEF_WIN, 25, 5, 10),
        SubGameResult(2, Outcome.VOID, 0, 0, 0, void=True),
    ], {"cop": 25, "thief": 15})
    jsonl = _jsonl(tmp_path, [{"event": "api_call", "input_tokens": 100, "output_tokens": 50}])
    summary = build_run_summary(series, jsonl)
    assert summary["valid_sub_games"] == 2
    assert summary["cost"]["api_calls"] == 1
    md = summary_markdown(summary)
    assert "Run summary" in md and "cop_win" in md and "✗" in md
