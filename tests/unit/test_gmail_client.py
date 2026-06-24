"""Tests for the Gmail client — dry-run + mocked live send (no network)."""

from __future__ import annotations

import base64
import email
import json

from robocop_mcp.reporting.gmail_client import GmailClient, encode_message
from robocop_mcp.sdk.sdk import MarlSDK
from robocop_mcp.shared.gatekeeper import ApiGatekeeper

_REPORT = {"group_name": "il-nv-ai", "totals": {"cop": 120, "thief": 30}}


def _gatekeeper(tmp_path) -> ApiGatekeeper:
    limits = {"requests_per_minute": 50, "requests_per_hour": 100,
              "retry_after_seconds": 0, "max_retries": 1, "max_queue_depth": 5}
    return ApiGatekeeper(limits, service="gmail", jsonl=tmp_path / "e.jsonl")


def test_encode_message_is_json_body() -> None:
    payload = encode_message("a@b.com", "subj", '{"x": 1}')
    msg = email.message_from_bytes(base64.urlsafe_b64decode(payload["raw"]))
    assert msg["to"] == "a@b.com" and msg["subject"] == "subj"
    # The body decodes back to exactly the JSON we passed (no prose added).
    assert msg.get_payload(decode=True).decode() == '{"x": 1}'


def test_dry_run_writes_json_only(tmp_path) -> None:
    client = GmailClient(_gatekeeper(tmp_path), jsonl=tmp_path / "e.jsonl")
    res = client.send(_REPORT, "r@x.com", dry_run=True, out_dir=tmp_path)
    assert res["dry_run"] is True
    report_path = tmp_path / "report_internal.json"
    assert json.loads(report_path.read_text())["group_name"] == "il-nv-ai"
    # The email body must be valid JSON with no surrounding prose.
    body = (tmp_path / "email_body.txt").read_text()
    assert json.loads(body)["totals"]["cop"] == 120


def test_live_send_uses_mocked_service(tmp_path) -> None:
    sent = {}

    class _Send:
        def __init__(self, **kw):
            sent.update(kw)

        def execute(self):
            return {"id": "msg-123"}

    class _Messages:
        def send(self, **kw):
            return _Send(**kw)

    class _Users:
        def messages(self):
            return _Messages()

    class _Service:
        def users(self):
            return _Users()

    client = GmailClient(_gatekeeper(tmp_path), service_factory=_Service, jsonl=tmp_path / "e.jsonl")
    res = client.send(_REPORT, "r@x.com", dry_run=False)
    assert res["sent"] is True and res["message_id"] == "msg-123"
    assert sent["userId"] == "me"


def test_sdk_send_report_dry_run(temp_config, tmp_path) -> None:
    sdk = MarlSDK(config=temp_config, token="t")
    series = sdk.run_series()
    res = sdk.send_report(series, dry_run=True, out_dir=tmp_path)
    assert res["dry_run"] is True
    assert (tmp_path / "report_internal.json").is_file()


def test_sdk_send_report_blocks_incomplete(temp_config, tmp_path) -> None:
    import pytest

    from robocop_mcp.constants import Outcome
    from robocop_mcp.domain.models import SubGameResult
    from robocop_mcp.orchestrator.orchestrator import SeriesResult

    sdk = MarlSDK(config=temp_config, token="t")
    incomplete = SeriesResult("m", [SubGameResult(0, Outcome.COP_WIN, 8, 20, 5)],
                              {"cop": 20, "thief": 5})
    with pytest.raises(ValueError, match="will not email"):
        sdk.send_report(incomplete, dry_run=True, out_dir=tmp_path)
