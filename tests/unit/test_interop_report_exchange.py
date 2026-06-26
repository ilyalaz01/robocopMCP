"""Tests for the final report-hash exchange (push results + pull opponent hash)."""

from __future__ import annotations

import asyncio

from robocop_mcp.interop.finalize import comparable_hash
from robocop_mcp.interop.report_exchange import (
    fetch_opponent_report_hash,
    push_our_results,
)

REPORT = {"sub_games": [{"sub_game_index": 1, "terminal_reason": "cop_capture",
                         "winner_role": "cop", "scores": {"cop": 20, "robber": 5},
                         "log_hash": "h1"}]}


class _Agree:
    """Opponent that records results and returns a report hash via confirm_final_report."""

    def __init__(self, report_hash: str) -> None:
        self.report_hash = report_hash
        self.pushed: list[int] = []

    async def confirm_sub_game_result(self, index, result_hash, body):
        self.pushed.append(index)
        return {"status": "recorded", "sub_game_index": index}

    async def confirm_final_report(self, report_hash):
        return {"status": "verified", "report_hash": self.report_hash}


class _NoTool:
    """Team B's actual behaviour: records but exposes no hash-returning tool."""

    async def confirm_sub_game_result(self, index, result_hash, body):
        return {"status": "recorded"}

    async def confirm_final_report(self, report_hash):
        return {"raw": "Unknown tool: confirm_final_report"}

    async def get_final_report(self):
        return {"raw": "Unknown tool: get_final_report"}


def test_push_results_sends_every_sub_game() -> None:
    opp = _Agree("a" * 64)
    asyncio.run(push_our_results(opp, REPORT))
    assert opp.pushed == [1]


def test_fetch_hash_from_field() -> None:
    opp = _Agree("b" * 64)
    assert asyncio.run(fetch_opponent_report_hash(opp, "ours")) == "b" * 64


def test_fetch_hash_by_hashing_their_report_dict() -> None:
    rep = {"sub_games": [], "totals_by_group": {}}

    class _WithReport:
        async def confirm_final_report(self, report_hash):
            return {"report": rep}

    got = asyncio.run(fetch_opponent_report_hash(_WithReport(), "ours"))
    assert got == comparable_hash(rep)


def test_fetch_none_when_no_tool() -> None:
    assert asyncio.run(fetch_opponent_report_hash(_NoTool(), "ours")) is None
