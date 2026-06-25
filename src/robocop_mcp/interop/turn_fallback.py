"""Fallback opponent endpoint + lazy sub-game init for bare ``take_turn`` calls.

Team B coordinates the live match: their runner calls OUR ``take_turn`` on ``/rpc``.
Normally they call ``start_sub_game`` first (which records ``opponent_url`` and starts
our inferred game). For a bare connectivity smoke (``take_turn`` with no prior
``start_sub_game``) we fall back to the opponent endpoint declared in
``config/config_interop.json`` and lazily start a default sub-game — so one
``take_turn`` still decides a move and makes exactly one outbound
``receive_action_message`` (never their ``take_turn`` → no recursion).
"""

from __future__ import annotations

import json
from pathlib import Path

from ..constants import Role
from ..domain.models import Position
from .game_adapter import ROLE_FROM_STR

_CFG = Path(__file__).resolve().parents[3] / "config" / "config_interop.json"

# Default placement for a lazily-started smoke sub-game (chess c3 / a1).
_DEFAULT_COP = Position(2, 2)
_DEFAULT_ROBBER = Position(0, 0)


def opponent_fallback() -> tuple[str | None, str | None]:
    """Return (url, token) of the opponent's MCP endpoint from config, else (None, None)."""
    try:
        opp = json.loads(_CFG.read_text()).get("opponent", {})
    except (OSError, json.JSONDecodeError):
        return None, None
    return opp.get("url"), opp.get("token")


def ensure_sub_game(agent, actor: str, rules) -> None:
    """Start a default sub-game iff none is active, so a bare take_turn can still act."""
    if agent.game is None:
        agent.start_sub_game(ROLE_FROM_STR.get(actor, Role.COP),
                             _DEFAULT_COP, _DEFAULT_ROBBER, rules)
