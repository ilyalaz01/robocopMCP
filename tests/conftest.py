"""Shared pytest fixtures (rubric §5.1.4).

All external dependencies (Anthropic, Gmail, network) are mocked in tests; no
fixture here ever touches the network.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from robocop_mcp.shared.config import ConfigManager

_BASE_GAME = {
    "version": "1.00",
    "grid_size": [5, 5],
    "max_moves": 25,
    "num_games": 6,
    "max_barriers": 5,
    "vision_radius": 1,
    "scoring": {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5},
    "llm": {"model": "test-model", "max_tokens": 256, "temperature": 0.0, "timeout_seconds": 5},
    "negotiation": {
        "max_rounds": 6,
        "allow_rule_changes": True,
        "negotiable": ["max_barriers", "grid_size", "num_cops"],
        "inviolable": ["thief_must_evade", "turn_based", "capture_ends_subgame"],
    },
    "q_learning": {
        "alpha": 0.1, "gamma": 0.9, "epsilon": 0.2, "epsilon_decay": 0.99,
        "min_epsilon": 0.01, "episodes": 50, "step_penalty": -1.0,
        "capture_reward": 50.0, "survive_reward": 1.0,
    },
    "servers": {
        "cop_host": "127.0.0.1", "cop_port": 8001,
        "thief_host": "127.0.0.1", "thief_port": 8002,
        "auth_token_env": "ROBOCOP_MCP_TOKEN", "default_token": "test-token",
    },
    "report": {"recipient_email": "rmisegal+uoh26b@gmail.com", "timezone": "Asia/Jerusalem"},
}

_RATE_LIMITS = {
    "rate_limits": {
        "version": "1.00",
        "services": {
            "default": {
                "requests_per_minute": 30, "requests_per_hour": 500,
                "concurrent_max": 5, "retry_after_seconds": 1,
                "max_retries": 3, "max_queue_depth": 10,
            }
        },
    }
}

_LOGGING = {
    "version": "1.00", "log_dir": "logs", "results_dir": "results",
    "level": "INFO", "jsonl_event_file": "events.jsonl",
    "human_log_file": "robocop.log", "console": False,
}


@pytest.fixture
def temp_config(tmp_path: Path) -> ConfigManager:
    """A ConfigManager backed by isolated temp config files.

    WHY copies, not the repo config: tests mutate values (grid size, episodes)
    and must never depend on or corrupt the committed config.
    """
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    (cfg_dir / "config.json").write_text(json.dumps(_BASE_GAME))
    (cfg_dir / "rate_limits.json").write_text(json.dumps(_RATE_LIMITS))
    (cfg_dir / "logging_config.json").write_text(json.dumps(_LOGGING))
    return ConfigManager(config_dir=cfg_dir)


@pytest.fixture
def base_game_config() -> dict:
    """A fresh deep-ish copy of the canonical game-config dict for unit tests."""
    return json.loads(json.dumps(_BASE_GAME))
