"""Integration: a full BONUS-profile series, both agents local, mocked LLM.

Proves the host-authoritative bonus mode end to end (ADR-0002/0003): full
visibility (open information), no deception (truthful persona), fixed start
pairs, a converged negotiation, and an exact-schema bonus report — all over real
MCP tool calls with the LLM mocked (no network).
"""

from __future__ import annotations

from robocop_mcp.constants import Role
from robocop_mcp.domain.engine import GameEngine
from robocop_mcp.domain.models import Position
from robocop_mcp.domain.starts import generate_starts
from robocop_mcp.orchestrator.turn_loop import make_llm_decider
from robocop_mcp.sdk.sdk import MarlSDK
from robocop_mcp.shared.config import ConfigManager


class _TruthfulLang:
    """A mocked, deception-free language engine (no network)."""

    deception = False

    def message(self, role, obs, msgs, suggestion) -> str:
        return f"[{role.value}] honestly moving {suggestion}."

    def interpret(self, role, text) -> str:
        return "NEAR"


def test_bonus_series_full_visibility_no_deception(tmp_path) -> None:
    sdk = MarlSDK(config=ConfigManager(profile="bonus"), token="t")
    assert sdk.rules.visibility == "full" and sdk.rules.deception is False

    # Brief negotiation converges on the SHARED_RULES values, both confirm.
    neg = sdk.negotiate(stance="agree", match_id="bonus_local")
    assert neg["confirmed"] is True
    assert neg["agreed_rules"] == {"max_barriers": 5, "max_moves": 25}

    decider = make_llm_decider(_TruthfulLang(), sdk.jsonl)
    series = sdk.run_series(decider=decider, match_id="bonus_local")
    assert len(series.sub_games) == 6

    # Host produces the exact-schema bonus JSON; mutual_agreement set true.
    opponent = {"group_name": "team-b", "github_repo": "gh-b", "students": [],
                "their_cop_url": "c", "their_thief_url": "t"}
    report = sdk.build_bonus_report(series, opponent, mutual_agreement=True)
    assert report["report_type"] == "bonus_game"
    assert report["groups"]["group_1"] == "il-nv-ai"
    assert report["mutual_agreement"] is True
    assert len(report["sub_games"]) == 6


def test_bonus_full_visibility_reveals_distant_opponent() -> None:
    sdk = MarlSDK(config=ConfigManager(profile="bonus"), token="t")
    engine = GameEngine(sdk.rules)
    engine.reset(cop=Position(0, 0), thief=Position(4, 4))  # Chebyshev distance 4
    # Full visibility ⇒ opponent seen despite being far outside vision_radius.
    assert engine.observe(Role.COP).opponent_pos == (4, 4)


def test_bonus_starts_are_six_distinct_pairs() -> None:
    sdk = MarlSDK(config=ConfigManager(profile="bonus"), token="t")
    starts = generate_starts(sdk.rules, 6)
    assert len({(c.as_tuple(), t.as_tuple()) for c, t in starts}) == 6
