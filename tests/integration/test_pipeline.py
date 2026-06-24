"""Integration: the full heuristic pipeline over in-memory MCP (no LLM, no net).

Proves the orchestrator drives complete sub-games and a 6-sub-game series end to
end over real MCP tool calls, including the technical-loss/void re-run path.
"""

from __future__ import annotations

import asyncio

from robocop_mcp.constants import Outcome, Role
from robocop_mcp.domain.models import MatchRules
from robocop_mcp.mcp.server_app import make_server
from robocop_mcp.mcp.session import SessionRegistry
from robocop_mcp.orchestrator.orchestrator import Orchestrator
from robocop_mcp.sdk.sdk import MarlSDK


def _orchestrator(rules: MatchRules, tmp_path, max_void_retries: int = 3):
    registry = SessionRegistry()
    jsonl = tmp_path / "events.jsonl"
    cop = make_server(Role.COP, "t", registry, None)
    thief = make_server(Role.THIEF, "t", registry, None)
    return Orchestrator(cop, thief, "t", registry, jsonl, max_void_retries), jsonl


def test_full_series_completes(temp_config) -> None:
    sdk = MarlSDK(config=temp_config, token="t")
    result = sdk.run_series()
    assert len(result.sub_games) == sdk.rules.num_games
    assert set(result.totals) == {"cop", "thief"}
    # Every recorded sub-game has a terminal (non-ongoing) outcome.
    assert all(sg.outcome is not Outcome.ONGOING for sg in result.sub_games)


def test_single_subgame_small_board(base_game_config, tmp_path) -> None:
    cfg = dict(base_game_config)
    cfg["grid_size"] = [3, 3]
    rules = MatchRules.from_config(cfg).with_overrides(num_games=1)
    orch, jsonl = _orchestrator(rules, tmp_path)
    result = asyncio.run(orch.run_series(rules, match_id="t3"))
    assert len(result.sub_games) == 1
    assert "turn" in jsonl.read_text()  # per-turn events were logged


def test_void_path_records_void(base_game_config, tmp_path) -> None:
    rules = MatchRules.from_config(base_game_config).with_overrides(num_games=1)
    orch, _ = _orchestrator(rules, tmp_path, max_void_retries=1)

    def bad_decider(role, obs, msgs, sug):
        # Thief tries to STAY (illegal) → move fails → sub-game voids.
        return "stalling", ("move", "STAY")

    result = asyncio.run(orch.run_series(rules, decider=bad_decider, match_id="void"))
    assert len(result.sub_games) == 1
    assert result.sub_games[0].void is True
