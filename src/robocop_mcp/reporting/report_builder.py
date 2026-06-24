"""Report builders — internal + inter-group bonus JSON (SPEC §11).

Field names match the assignment EXACTLY so the grader's system can parse the
emailed JSON. The Cop emails the internal report once all sub-games are valid;
the bonus report is assembled with the other team's details for Phase 11.
"""

from __future__ import annotations

from ..constants import GITHUB_REPO, GROUP_CODE, STUDENTS


def _sub_game_rows(series) -> list[dict]:
    """Serialize each sub-game with its outcome and per-side scores."""
    return [
        {"index": sg.index, "outcome": sg.outcome.value, "moves": sg.moves,
         "cop_score": sg.cop_score, "thief_score": sg.thief_score, "void": sg.void}
        for sg in series.sub_games
    ]


def mcp_url(host: str, port: int) -> str:
    """Build a server's MCP URL from host/port (Ilya swaps in public URLs later)."""
    return f"http://{host}:{port}/mcp/"


def build_internal_report(series, config, cop_url: str, thief_url: str) -> dict:
    """Build the mandatory single-group report (both agents ours)."""
    return {
        "group_name": GROUP_CODE,
        "students": [dict(s) for s in STUDENTS],
        "github_repo": GITHUB_REPO,
        "cop_mcp_url": cop_url,
        "thief_mcp_url": thief_url,
        "timezone": config.get("report", "timezone", default="Asia/Jerusalem"),
        "sub_games": _sub_game_rows(series),
        "totals": series.totals,
    }


def build_bonus_report(series, config, opponent: dict, mutual_agreement: dict,
                       bonus_claim: bool = True) -> dict:
    """Build the two-group bonus report (our group = group_1).

    ``opponent`` supplies group_2's identity + URLs (provided by Ilya in Phase 11).
    """
    tz = config.get("report", "timezone", default="Asia/Jerusalem")
    return {
        "report_type": "bonus_game",
        "groups": {"group_1": GROUP_CODE, "group_2": opponent.get("group_name", "")},
        "github_repo_group_1": GITHUB_REPO,
        "github_repo_group_2": opponent.get("github_repo", ""),
        "mcp_url_group_1_cop": opponent.get("our_cop_url", ""),
        "mcp_url_group_1_thief": opponent.get("our_thief_url", ""),
        "mcp_url_group_2_cop": opponent.get("their_cop_url", ""),
        "mcp_url_group_2_thief": opponent.get("their_thief_url", ""),
        "timezone": tz,
        "students_group_1": [dict(s) for s in STUDENTS],
        "students_group_2": opponent.get("students", []),
        "sub_games": _sub_game_rows(series),
        "totals_by_group": {"group_1": series.totals, "group_2": opponent.get("totals", {})},
        "bonus_claim": bonus_claim,
        "mutual_agreement": mutual_agreement,
    }


def count_valid(series) -> int:
    """Number of non-void sub-games — the Cop emails only when this hits num_games."""
    return sum(1 for sg in series.sub_games if not sg.void)
