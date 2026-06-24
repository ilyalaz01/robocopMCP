"""Tests for the negotiation driver + SDK negotiate (mocked, no network)."""

from __future__ import annotations

import asyncio

from fastmcp import Client

from robocop_mcp.constants import Role
from robocop_mcp.domain.models import MatchRules
from robocop_mcp.mcp.server_app import make_server
from robocop_mcp.mcp.session import SessionRegistry
from robocop_mcp.orchestrator.negotiation import (
    NegotiationDriver,
    template_speaker,
    write_negotiation_md,
)
from robocop_mcp.sdk.sdk import MarlSDK


def _drive(base_game_config, tmp_path, stance, max_rounds=4):
    registry = SessionRegistry()
    registry.create("m-neg", MatchRules.from_config(base_game_config))
    cop = make_server(Role.COP, "t", registry, None)
    thief = make_server(Role.THIEF, "t", registry, None)
    jsonl = tmp_path / "e.jsonl"

    async def go():
        async with Client(cop) as cc, Client(thief) as tc:
            driver = NegotiationDriver(cc, tc, "t", "m-neg", jsonl, template_speaker)
            return await driver.negotiate({"max_barriers": 5}, stance, max_rounds)

    return asyncio.run(go()), registry


def test_easy_agree_path(base_game_config, tmp_path) -> None:
    result, _ = _drive(base_game_config, tmp_path, "agree")
    assert result["confirmed"] is True
    assert result["conceded"] is False
    assert result["agreed_rules"] == {"max_barriers": 5}


def test_must_concede_path(base_game_config, tmp_path) -> None:
    result, registry = _drive(base_game_config, tmp_path, "counter", max_rounds=3)
    assert result["confirmed"] is True
    assert result["conceded"] is True
    # Conceded to the Thief's last counter (more barriers than proposed).
    assert result["agreed_rules"]["max_barriers"] > 5


def test_template_speaker() -> None:
    assert template_speaker(Role.COP, "propose", "x") == "[cop] propose: x"


def test_write_negotiation_md(base_game_config, tmp_path) -> None:
    _, registry = _drive(base_game_config, tmp_path, "agree")
    path = write_negotiation_md(registry.get("m-neg"), tmp_path / "results", "m")
    text = path.read_text()
    assert "Negotiation" in text and "cop" in text and "thief" in text


def test_sdk_negotiate_applies_agreement(temp_config) -> None:
    sdk = MarlSDK(config=temp_config, token="t")
    result = sdk.negotiate(stance="counter", match_id="appl")
    assert result["confirmed"] and result["conceded"]
    # The agreed (conceded) barrier count is now reflected in the effective rules.
    assert sdk.rules.max_barriers == result["agreed_rules"]["max_barriers"]


def test_sdk_apply_agreement_grid_size(temp_config) -> None:
    sdk = MarlSDK(config=temp_config, token="t")
    rules = sdk._apply_agreement({"grid_size": [4, 4], "max_barriers": 3})
    assert rules.grid_width == 4 and rules.grid_height == 4
    assert rules.thief_start.as_tuple() == (3, 3)
    assert rules.max_barriers == 3


def test_sdk_run_sub_game(temp_config) -> None:
    sdk = MarlSDK(config=temp_config, token="t")
    result = sdk.run_sub_game()
    assert len(result.sub_games) == 1
