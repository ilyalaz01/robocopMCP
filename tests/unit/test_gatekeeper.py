"""Tests for ApiGatekeeper — pass-through, queue/drain, backpressure, retry, log."""

from __future__ import annotations

import json

import pytest

from robocop_mcp.shared.gatekeeper import ApiGatekeeper, QueueFullError


class _Clock:
    """A controllable clock whose injected sleep advances virtual time."""

    def __init__(self) -> None:
        self.t = 0.0

    def now(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.t += seconds


def _limits(**over) -> dict:
    base = {
        "requests_per_minute": 30, "requests_per_hour": 500,
        "retry_after_seconds": 30, "max_retries": 3, "max_queue_depth": 10,
    }
    base.update(over)
    return base


class _Usage:
    input_tokens, output_tokens = 12, 34


class _Result:
    usage = _Usage()


def test_passthrough_and_token_logging(tmp_path) -> None:
    jsonl = tmp_path / "e.jsonl"
    gk = ApiGatekeeper(_limits(), service="anthropic", jsonl=jsonl)
    result = gk.execute(lambda x: _Result(), 1)
    assert isinstance(result, _Result)
    assert gk.get_queue_status().processed == 1
    logged = [json.loads(line) for line in jsonl.read_text().splitlines()]
    call = next(e for e in logged if e["event"] == "api_call")
    assert call["input_tokens"] == 12 and call["output_tokens"] == 34


def test_queue_then_drain(tmp_path) -> None:
    clock = _Clock()
    gk = ApiGatekeeper(_limits(requests_per_minute=2), jsonl=tmp_path / "e.jsonl",
                       clock=clock.now, sleep=clock.sleep)
    for _ in range(2):
        gk.execute(lambda: "ok")
    # Third call has no slot → it queues, then drains once virtual time passes 60s.
    assert gk.execute(lambda: "drained") == "drained"
    status = gk.get_queue_status()
    assert status.queued == 1 and status.depth == 0 and status.processed == 3


def test_backpressure_when_queue_full(tmp_path) -> None:
    gk = ApiGatekeeper(_limits(requests_per_minute=1, max_queue_depth=0),
                       jsonl=tmp_path / "e.jsonl")
    gk.execute(lambda: "ok")
    with pytest.raises(QueueFullError):
        gk.execute(lambda: "rejected")
    assert gk.get_queue_status().rejected == 1


def test_retry_transient_then_success(tmp_path) -> None:
    clock = _Clock()
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise TimeoutError("transient")
        return "recovered"

    gk = ApiGatekeeper(_limits(), jsonl=tmp_path / "e.jsonl", clock=clock.now, sleep=clock.sleep)
    assert gk.execute(flaky) == "recovered"
    assert gk.get_queue_status().retries == 2


def test_permanent_error_propagates(tmp_path) -> None:
    gk = ApiGatekeeper(_limits(), jsonl=tmp_path / "e.jsonl")
    with pytest.raises(ValueError):
        gk.execute(lambda: (_ for _ in ()).throw(ValueError("permanent")))


def test_exceeds_max_retries(tmp_path) -> None:
    clock = _Clock()
    gk = ApiGatekeeper(_limits(max_retries=2), jsonl=tmp_path / "e.jsonl",
                       clock=clock.now, sleep=clock.sleep)
    with pytest.raises(TimeoutError):
        gk.execute(lambda: (_ for _ in ()).throw(TimeoutError("always")))


def test_from_config(temp_config) -> None:
    gk = ApiGatekeeper.from_config(temp_config, "anthropic")
    assert gk.service == "anthropic"  # falls back to default service in test config
