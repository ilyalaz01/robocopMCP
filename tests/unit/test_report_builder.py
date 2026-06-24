"""Tests for the internal + bonus report builders (exact-schema validation)."""

from __future__ import annotations

from robocop_mcp.constants import Outcome
from robocop_mcp.domain.models import SubGameResult
from robocop_mcp.orchestrator.orchestrator import SeriesResult
from robocop_mcp.reporting.report_builder import (
    build_bonus_report,
    build_internal_report,
    count_valid,
    mcp_url,
)


def _series() -> SeriesResult:
    games = [SubGameResult(i, Outcome.COP_WIN, 8, 20, 5) for i in range(6)]
    return SeriesResult("m", games, {"cop": 120, "thief": 30})


def test_mcp_url() -> None:
    assert mcp_url("127.0.0.1", 8001) == "http://127.0.0.1:8001/mcp/"


def test_internal_report_exact_schema(temp_config) -> None:
    report = build_internal_report(_series(), temp_config, "cop_url", "thief_url")
    assert set(report) == {
        "group_name", "students", "github_repo", "cop_mcp_url", "thief_mcp_url",
        "timezone", "sub_games", "totals",
    }
    assert report["group_name"] == "il-nv-ai"
    assert report["totals"] == {"cop": 120, "thief": 30}
    assert len(report["sub_games"]) == 6
    assert report["sub_games"][0]["outcome"] == "cop_win"
    assert {s["id"] for s in report["students"]} == {"212177943", "316350768"}


def test_bonus_report_exact_schema(temp_config) -> None:
    opponent = {"group_name": "other", "github_repo": "gh2", "students": [],
                "their_cop_url": "c2", "their_thief_url": "t2", "totals": {"cop": 5}}
    report = build_bonus_report(_series(), temp_config, opponent,
                                {"max_barriers": 7}, bonus_claim=True)
    assert report["report_type"] == "bonus_game"
    for key in ("groups", "github_repo_group_1", "github_repo_group_2",
                "mcp_url_group_1_cop", "mcp_url_group_2_thief", "students_group_1",
                "totals_by_group", "bonus_claim", "mutual_agreement"):
        assert key in report
    assert report["groups"]["group_1"] == "il-nv-ai"
    assert report["mutual_agreement"] == {"max_barriers": 7}


def test_count_valid_excludes_void() -> None:
    games = [SubGameResult(0, Outcome.COP_WIN, 8, 20, 5),
             SubGameResult(1, Outcome.VOID, 0, 0, 0, void=True)]
    series = SeriesResult("m", games, {"cop": 20, "thief": 5})
    assert count_valid(series) == 1
