"""Tests for ConfigManager — version validation + nested lookup (Phase 0)."""

from __future__ import annotations

import json

import pytest

from robocop_mcp.shared.config import ConfigError, ConfigManager


def test_loads_game_config(temp_config: ConfigManager) -> None:
    cfg = temp_config.game()
    assert cfg["version"] == "1.00"
    assert cfg["grid_size"] == [5, 5]


def test_rate_limits_unwraps_inner(temp_config: ConfigManager) -> None:
    rl = temp_config.rate_limits()
    assert rl["version"] == "1.00"
    assert rl["services"]["default"]["requests_per_minute"] == 30


def test_logging_config(temp_config: ConfigManager) -> None:
    assert temp_config.logging()["jsonl_event_file"] == "events.jsonl"


def test_nested_get(temp_config: ConfigManager) -> None:
    assert temp_config.get("scoring", "cop_win") == 20
    assert temp_config.get("missing", "key", default=42) == 42
    assert temp_config.get("scoring", "nope", default=7) == 7


def test_caching_returns_same_object(temp_config: ConfigManager) -> None:
    assert temp_config.game() is temp_config.game()


def test_missing_file_raises(tmp_path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        ConfigManager(config_dir=tmp_path).game()


def test_bad_version_raises(tmp_path) -> None:
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    (cfg_dir / "config.json").write_text(json.dumps({"version": "9.99"}))
    with pytest.raises(ConfigError, match="Incompatible config version"):
        ConfigManager(config_dir=cfg_dir).game()


def test_real_repo_config_is_valid() -> None:
    """The committed config files must load + validate (guards against typos)."""
    cfg = ConfigManager()
    assert cfg.game()["version"] == "1.00"
    assert cfg.rate_limits()["version"] == "1.00"
    assert cfg.logging()["version"] == "1.00"
    assert cfg.root.is_dir()
