"""GameSession + SessionRegistry — the authoritative shared state (ADR-0002).

For local play both MCP servers run in the same process and reach one
``GameSession`` through a module-level ``SessionRegistry``. The session wraps
the pure :class:`GameEngine` and adds the cross-cutting concerns the servers
need: a natural-language mailbox and the negotiation scratchpad. For inter-team
play the registry is swapped for a networked store (see ADR-0002 / SPEC §12).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from ..constants import Role
from ..domain.engine import GameEngine
from ..domain.models import MatchRules


@dataclass
class Message:
    """One natural-language message posted to the shared mailbox."""

    sender: str
    text: str
    move_count: int
    ts: float = field(default_factory=time.time)

    def as_dict(self) -> dict:
        """JSON-friendly form for tool results and transcripts."""
        return {"sender": self.sender, "text": self.text, "move_count": self.move_count}


class GameSession:
    """Authoritative state for one match: engine + mailbox + negotiation."""

    def __init__(self, session_id: str, rules: MatchRules) -> None:
        self.session_id = session_id
        self.rules = rules
        self.engine = GameEngine(rules)
        self.mailbox: list[Message] = []
        # Negotiation scratchpad — proposals/confirmations keyed by role.
        self.proposals: list[dict] = []
        self.confirmations: dict[str, bool] = {Role.COP.value: False, Role.THIEF.value: False}
        self.agreed_rules: dict | None = None

    def post_message(self, sender: Role, text: str) -> Message:
        """Append a message from ``sender`` to the shared mailbox."""
        msg = Message(sender=sender.value, text=text, move_count=self.engine.state.move_count)
        self.mailbox.append(msg)
        return msg

    def read_for(self, reader: Role, limit: int = 5) -> list[dict]:
        """Return the opponent's most recent messages (what ``reader`` may read)."""
        opponent = Role.THIEF.value if reader is Role.COP else Role.COP.value
        msgs = [m for m in self.mailbox if m.sender == opponent]
        return [m.as_dict() for m in msgs[-limit:]]

    def both_confirmed(self) -> bool:
        """True once both agents have called ``negotiate_confirm``."""
        return all(self.confirmations.values())


class SessionRegistry:
    """In-process registry mapping ``session_id`` → :class:`GameSession`."""

    def __init__(self) -> None:
        self._sessions: dict[str, GameSession] = {}

    def create(self, session_id: str, rules: MatchRules) -> GameSession:
        """Create (or replace) a session and return it."""
        session = GameSession(session_id, rules)
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> GameSession | None:
        """Look up a session, or ``None`` if absent."""
        return self._sessions.get(session_id)

    def drop(self, session_id: str) -> None:
        """Remove a session (cleanup between matches)."""
        self._sessions.pop(session_id, None)


# Module-level singleton shared by both servers for local play.
REGISTRY = SessionRegistry()
