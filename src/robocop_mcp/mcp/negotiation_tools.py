"""Negotiation tools mixin — propose / respond / confirm (SPEC §7).

One concern only (pre-game rule negotiation), mixed into
:class:`~robocop_mcp.mcp.tools.AgentToolService`. It relies on the host class
providing ``registry``, ``role``, ``_auth``, and ``_log`` — documented here so
the mixin stays independently reviewable (rubric §3.2).
"""

from __future__ import annotations

from typing import Any


class NegotiationMixin:
    """Adds the three negotiation tools to an agent tool service."""

    def negotiate_propose(self, session_id: str, token: str, rules: dict, message: str) -> dict:
        """Propose a ruleset plus a natural-language argument for it."""
        err = self._auth(token)  # type: ignore[attr-defined]
        if err:
            return err
        session = self.registry.get(session_id)  # type: ignore[attr-defined]
        if session is None:
            return {"ok": False, "error": "no_session"}
        proposal: dict[str, Any] = {
            "by": self.role.value, "rules": rules, "message": message,  # type: ignore[attr-defined]
        }
        session.proposals.append(proposal)
        session.post_message(self.role, message)  # type: ignore[attr-defined]
        self._log("negotiate_propose", session_id, ok=True, rules=rules)  # type: ignore[attr-defined]
        return {"ok": True, "proposal": proposal}

    def negotiate_respond(
        self, session_id: str, token: str, accept: bool, counter_rules: dict, message: str
    ) -> dict:
        """Accept the latest proposal, or counter it with adjusted rules."""
        err = self._auth(token)  # type: ignore[attr-defined]
        if err:
            return err
        session = self.registry.get(session_id)  # type: ignore[attr-defined]
        if session is None:
            return {"ok": False, "error": "no_session"}
        response = {
            "by": self.role.value, "accept": accept,  # type: ignore[attr-defined]
            "counter_rules": counter_rules, "message": message,
        }
        session.proposals.append(response)
        session.post_message(self.role, message)  # type: ignore[attr-defined]
        if accept and session.proposals:
            # Adopt the most recent concrete ruleset as the working agreement.
            for prior in reversed(session.proposals):
                if prior.get("rules"):
                    session.agreed_rules = prior["rules"]
                    break
        self._log("negotiate_respond", session_id, ok=True, accept=accept)  # type: ignore[attr-defined]
        return {"ok": True, "response": response, "agreed_rules": session.agreed_rules}

    def negotiate_confirm(self, session_id: str, token: str, message: str) -> dict:
        """Explicitly confirm; play starts only when BOTH roles have confirmed."""
        err = self._auth(token)  # type: ignore[attr-defined]
        if err:
            return err
        session = self.registry.get(session_id)  # type: ignore[attr-defined]
        if session is None:
            return {"ok": False, "error": "no_session"}
        session.confirmations[self.role.value] = True  # type: ignore[attr-defined]
        session.post_message(self.role, message)  # type: ignore[attr-defined]
        both = session.both_confirmed()
        self._log("negotiate_confirm", session_id, ok=True, both=both)  # type: ignore[attr-defined]
        return {"ok": True, "both_confirmed": both, "agreed_rules": session.agreed_rules}
