"""AgentToolService — the shared, token-guarded implementation of every MCP tool.

The two FastMCP servers (cop/thief) are thin wrappers that register one of these
services and forward calls; all logic lives here so it is fully unit-testable
without a network (rubric §3.1). Every tool requires the revocable token and is
logged to the JSONL event stream (SPEC §6/§13).
"""

from __future__ import annotations

from pathlib import Path

from ..agents.strategy import default_target, heuristic_action
from ..constants import Direction, Role
from ..domain.models import Position
from ..shared.logging_setup import log_event
from .negotiation_tools import NegotiationMixin
from .session import SessionRegistry


class AgentToolService(NegotiationMixin):
    """Implements one agent's MCP tools against a shared session registry.

    Setup:  registry, role (COP/THIEF), token (revocable), jsonl_path (log sink).
    """

    def __init__(
        self, registry: SessionRegistry, role: Role, token: str, jsonl_path: Path, qtable=None
    ) -> None:
        self.registry = registry
        self.role = role
        self.token = token
        self.jsonl_path = jsonl_path
        # When a trained Q-table is supplied, suggest_move uses it; else heuristic.
        self.qtable = qtable

    # --- internals -------------------------------------------------------
    def _auth(self, token: str) -> dict | None:
        """Return an error dict if the token is wrong/revoked, else ``None``."""
        if token != self.token:
            self._log("auth_reject", "-", ok=False)
            return {"ok": False, "error": "unauthorized: invalid or revoked token"}
        return None

    def _log(self, tool: str, session_id: str, **fields) -> None:
        """Record one tool call to the JSONL event stream."""
        log_event(self.jsonl_path, "tool_call", role=self.role.value, tool=tool,
                  session_id=session_id, **fields)

    def _session(self, session_id: str):
        """Fetch the session or ``None`` (caller returns no_session error)."""
        return self.registry.get(session_id)

    # --- observation / messaging ----------------------------------------
    def observe(self, session_id: str, token: str) -> dict:
        """Partial observation within ``vision_radius`` (SPEC §6)."""
        err = self._auth(token)
        if err:
            return err
        session = self._session(session_id)
        if session is None:
            return {"ok": False, "error": "no_session"}
        obs = session.engine.observe(self.role)
        self._log("observe", session_id, ok=True)
        return {"ok": True, "observation": vars(obs) | {"role": self.role.value,
                "self_pos": obs.self_pos.as_tuple()}}

    def read_messages(self, session_id: str, token: str) -> dict:
        """Return the opponent's latest natural-language messages."""
        err = self._auth(token)
        if err:
            return err
        session = self._session(session_id)
        if session is None:
            return {"ok": False, "error": "no_session"}
        msgs = session.read_for(self.role)
        self._log("read_messages", session_id, ok=True, count=len(msgs))
        return {"ok": True, "messages": msgs}

    def send_message(self, session_id: str, token: str, text: str) -> dict:
        """Post a natural-language message to the shared mailbox."""
        err = self._auth(token)
        if err:
            return err
        session = self._session(session_id)
        if session is None:
            return {"ok": False, "error": "no_session"}
        session.post_message(self.role, text)
        self._log("send_message", session_id, ok=True, text=text)
        return {"ok": True}

    # --- strategy / actions ---------------------------------------------
    def suggest_move(self, session_id: str, token: str) -> dict:
        """Recommend an action for the current state (heuristic until Q wired)."""
        err = self._auth(token)
        if err:
            return err
        session = self._session(session_id)
        if session is None:
            return {"ok": False, "error": "no_session"}
        eng = session.engine
        obs = eng.observe(self.role)
        if obs.opponent_pos is not None:
            target = Position(*obs.opponent_pos)
        else:
            target = default_target(self.role, eng.rules.cop_start, eng.rules.thief_start)
        own = eng.state.cop if self.role is Role.COP else eng.state.thief
        suggestion = self._suggest(eng, own, target)
        self._log("suggest_move", session_id, ok=True, suggestion=suggestion,
                  source="qtable" if self.qtable else "heuristic")
        return {"ok": True, "suggestion": suggestion}

    def _suggest(self, eng, own: Position, target: Position) -> str | None:
        """Pick an action from the Q-table if present, else the heuristic."""
        if self.qtable is not None:
            from ..learning.q_learning import encode_state
            from ..learning.trainer import legal_indices

            legal = legal_indices(eng, self.role, self.qtable.actions)
            if legal:
                idx = self.qtable.select(encode_state(own, target), legal, explore=False)
                return self.qtable.actions[idx]
            return None
        action = heuristic_action(self.role, own, target, eng.board, eng.state.barriers)
        return action.value if action else None

    def move(self, session_id: str, token: str, direction: str) -> dict:
        """Validate + apply a one-step move (mutual position verification)."""
        err = self._auth(token)
        if err:
            return err
        session = self._session(session_id)
        if session is None:
            return {"ok": False, "error": "no_session"}
        try:
            d = Direction(direction)
        except ValueError:
            return {"ok": False, "error": f"bad_direction: {direction!r}"}
        result = session.engine.apply_move(self.role, d)
        self._log("move", session_id, ok=result.ok, direction=direction, reason=result.reason)
        return {"ok": result.ok, "reason": result.reason, "digest": result.state_digest}

    def place_barrier(self, session_id: str, token: str) -> dict:
        """Cop-only: forfeit the move and mark the current cell impassable."""
        err = self._auth(token)
        if err:
            return err
        session = self._session(session_id)
        if session is None:
            return {"ok": False, "error": "no_session"}
        result = session.engine.place_barrier(self.role)
        self._log("place_barrier", session_id, ok=result.ok, reason=result.reason)
        return {"ok": result.ok, "reason": result.reason, "digest": result.state_digest}

    def match_digest(self, session_id: str, token: str) -> dict:
        """Compact authoritative snapshot for logging / mutual verification."""
        err = self._auth(token)
        if err:
            return err
        session = self._session(session_id)
        if session is None:
            return {"ok": False, "error": "no_session"}
        return {"ok": True, "digest": session.engine._digest()}
