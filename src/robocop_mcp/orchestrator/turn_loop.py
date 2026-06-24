"""Per-turn loop — drives one agent's turn over the MCP tools (SPEC §6.2).

The decision policy is injected as a ``decider`` callable so the same loop runs
with a deterministic heuristic (Phase 3) or a real LLM (Phase 5) without change.
Every tool exchange is logged; the loop never trusts the agent — the server's
``move`` re-validates each action.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..constants import Role
from ..shared.logging_setup import log_event

# A decider maps (role, observation, opponent_messages, suggestion) to an
# (message_text, action) pair, where action is ("move", direction) or
# ("barrier", None). Kept tiny so the LLM agent can drop in later.
Decider = Callable[[Role, dict, list, str | None], tuple[str, tuple[str, str | None]]]


async def _call(client: Any, name: str, **args: Any) -> dict:
    """Invoke an MCP tool and return its structured ``.data`` payload."""
    result = await client.call_tool(name, args)
    return result.data


def default_decider(
    role: Role, observation: dict, messages: list, suggestion: str | None
) -> tuple[str, tuple[str, str | None]]:
    """Deterministic heuristic policy used before the LLM is wired in.

    Follows the Q/heuristic ``suggestion``; if the agent is boxed in
    (``suggestion is None``) the Cop places a barrier and the Thief is reported
    trapped (the sub-game will resolve or be voided upstream).
    """
    step = observation.get("move_count", "?")
    if suggestion is None:
        if role is Role.COP:
            return f"[cop] turn {step}: no path — placing a barrier.", ("barrier", None)
        return f"[thief] turn {step}: cornered!", ("move", None)
    if suggestion == "PLACE_BARRIER":
        return f"[cop] turn {step}: walling off an escape route.", ("barrier", None)
    intent = "closing in" if role is Role.COP else "slipping away"
    return f"[{role.value}] turn {step}: {intent}, moving {suggestion}.", ("move", suggestion)


def _action_from_suggestion(role: Role, suggestion: str | None) -> tuple[str, str | None]:
    """Map a suggestion to a concrete action (shared by heuristic + LLM deciders)."""
    if suggestion == "PLACE_BARRIER" or (suggestion is None and role is Role.COP):
        return ("barrier", None)
    if suggestion is None:
        return ("move", None)
    return ("move", suggestion)


def make_llm_decider(language, jsonl=None) -> Decider:
    """Build a decider whose *message* is real Haiku and *move* is the Q-suggestion.

    SPEC §5: language is the LLM's job, movement is the Q-table's — they do not
    fight. The opponent's last message is interpreted into a logged belief.
    """
    def decide(role: Role, observation: dict, messages: list, suggestion: str | None):
        text = language.message(role, observation, messages, suggestion)
        if messages:
            belief = language.interpret(role, messages[-1]["text"])
            if jsonl is not None:
                log_event(jsonl, "belief", role=role.value, belief=belief)
        return text, _action_from_suggestion(role, suggestion)

    return decide


async def play_turn(
    client: Any, role: Role, token: str, session_id: str, jsonl, decider: Decider
) -> dict:
    """Run the active agent's full turn: observe → message → decide → act."""
    obs = (await _call(client, "observe", session_id=session_id, token=token)).get("observation", {})
    msgs = (await _call(client, "read_messages", session_id=session_id, token=token)).get(
        "messages", []
    )
    sug = (await _call(client, "suggest_move", session_id=session_id, token=token)).get("suggestion")

    message, (kind, direction) = decider(role, obs, msgs, sug)
    if message:
        await _call(client, "send_message", session_id=session_id, token=token, text=message)

    if kind == "barrier":
        res = await _call(client, "place_barrier", session_id=session_id, token=token)
    elif direction is None:
        res = {"ok": False, "reason": "no_legal_action"}
    else:
        res = await _call(client, "move", session_id=session_id, token=token, direction=direction)

    log_event(jsonl, "turn", role=role.value, session_id=session_id, message=message,
              action=kind, direction=direction, ok=res.get("ok"), reason=res.get("reason"))
    return res
