"""Tests for config profiles (solo/bonus) + ConfigManager selection/validation."""

from __future__ import annotations

import json

import pytest

from robocop_mcp.domain.models import MatchRules
from robocop_mcp.shared.config import ConfigError, ConfigManager


def test_default_profile_is_solo() -> None:
    cfg = ConfigManager()
    assert cfg.profile == "solo"
    g = cfg.game()
    assert g["visibility"] == "partial" and g["deception"] is True
    assert g["start_mode"] == "seeded_random" and g["start_seed"] == 42


def test_bonus_profile_loads_real_config() -> None:
    cfg = ConfigManager(profile="bonus")
    g = cfg.game()
    assert g["visibility"] == "full" and g["deception"] is False
    assert g["start_mode"] == "fixed_pairs"
    assert len(g["start_pairs"]) == 6
    # Converged negotiable values must equal SHARED_RULES (max_barriers 5, max_moves 25).
    assert g["max_barriers"] == 5 and g["max_moves"] == 25
    assert g["negotiation"]["converged"] == {"max_barriers": 5, "max_moves": 25}


def test_bonus_matchrules_has_six_distinct_pairs() -> None:
    rules = MatchRules.from_config(ConfigManager(profile="bonus").game())
    assert rules.visibility == "full" and rules.deception is False
    pairs = rules.start_pairs
    assert len(pairs) == 6
    assert len({(c.as_tuple(), t.as_tuple()) for c, t in pairs}) == 6  # all distinct
    assert all(c != t for c, t in pairs)  # non-overlapping


def test_env_var_selects_profile(monkeypatch) -> None:
    monkeypatch.setenv("ROBOCOP_PROFILE", "bonus")
    assert ConfigManager().profile == "bonus"


def test_unknown_profile_raises() -> None:
    with pytest.raises(ConfigError, match="Unknown profile"):
        ConfigManager(profile="nope")


def _write_game(tmp_path, **over) -> ConfigManager:
    base = json.loads((ConfigManager().root / "config" / "config.json").read_text())
    base.update(over)
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    (cfg_dir / "config.json").write_text(json.dumps(base))
    return ConfigManager(config_dir=cfg_dir, profile="solo")


def test_invalid_visibility_raises(tmp_path) -> None:
    with pytest.raises(ConfigError, match="visibility"):
        _write_game(tmp_path, visibility="sideways").game()


def test_invalid_start_mode_raises(tmp_path) -> None:
    with pytest.raises(ConfigError, match="start_mode"):
        _write_game(tmp_path, start_mode="teleport").game()


def test_non_bool_deception_raises(tmp_path) -> None:
    with pytest.raises(ConfigError, match="deception"):
        _write_game(tmp_path, deception="yes").game()
