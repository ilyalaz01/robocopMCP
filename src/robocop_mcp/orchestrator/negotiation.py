"""Pre-game negotiation driver — the star feature (SPEC §7).

Drives the two agents through propose → (counter)* → confirm over the MCP
negotiation tools, in natural language. Our persona proposes its own ruleset
first, argues briefly, and — if the other side stays firm to ``max_rounds`` —
concedes gracefully and plays by their rules. No sub-game starts until BOTH
agents explicitly confirm. The full dialogue is saved for the report.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from ..constants import Role
from ..shared.logging_setup import log_event
from .turn_loop import _call

# A speaker turns (role, intent, detail) into a natural-language line.
Speaker = Callable[[Role, str, str], str]


def template_speaker(role: Role, intent: str, detail: str) -> str:
    """Deterministic speaker used in tests and as the LLM fallback."""
    return f"[{role.value}] {intent}: {detail}"


def make_llm_speaker(language) -> Speaker:
    """Wrap a :class:`LanguageEngine` so negotiation lines come from Haiku."""
    return lambda role, intent, detail: language.negotiation_line(role, intent, detail)


class NegotiationDriver:
    """Runs one negotiation to a confirmed agreement over the MCP tools."""

    def __init__(self, cop_client, thief_client, token: str, session_id: str,
                 jsonl, speaker: Speaker = template_speaker) -> None:
        self.cop, self.thief = cop_client, thief_client
        self.token, self.session_id, self.jsonl = token, session_id, jsonl
        self.speak = speaker

    async def negotiate(self, proposal: dict, responder_stance: str, max_rounds: int) -> dict:
        """Negotiate ``proposal``; ``responder_stance`` is 'agree' or 'counter'.

        Returns ``{"agreed_rules", "confirmed", "rounds", "conceded"}``.
        """
        await self._propose(self.cop, proposal, "propose its preferred ruleset")
        agreed, conceded, rounds = proposal, False, 0

        for r in range(max_rounds):
            rounds = r + 1
            if responder_stance == "agree":
                agreed = await self._respond(self.thief, True, {}, "accept the fair proposal")
                break
            counter = {"max_barriers": int(proposal.get("max_barriers", 5)) + 1 + r}
            await self._respond(self.thief, False, counter, "counter with more barriers")
            if r == max_rounds - 1:
                agreed = await self._respond(self.cop, True, {}, "concede gracefully and accept")
                conceded = True
            else:
                await self._propose(self.cop, proposal, "argue briefly for its ruleset")

        confirmed = await self._confirm()
        log_event(self.jsonl, "negotiation_end", session_id=self.session_id,
                  agreed=agreed, confirmed=confirmed, rounds=rounds, conceded=conceded)
        return {"agreed_rules": agreed, "confirmed": confirmed, "rounds": rounds,
                "conceded": conceded}

    async def _propose(self, client, rules: dict, intent: str) -> None:
        await _call(client, "negotiate_propose", session_id=self.session_id, token=self.token,
                    rules=rules, message=self.speak(_role(client, self), intent, str(rules)))

    async def _respond(self, client, accept: bool, counter: dict, intent: str) -> dict:
        res = await _call(client, "negotiate_respond", session_id=self.session_id,
                          token=self.token, accept=accept, counter_rules=counter,
                          message=self.speak(_role(client, self), intent, str(counter)))
        return res.get("agreed_rules") or counter

    async def _confirm(self) -> bool:
        await _call(self.cop, "negotiate_confirm", session_id=self.session_id,
                    token=self.token, message=self.speak(Role.COP, "confirm", "ready to play"))
        res = await _call(self.thief, "negotiate_confirm", session_id=self.session_id,
                          token=self.token, message=self.speak(Role.THIEF, "confirm", "ready"))
        return bool(res.get("both_confirmed"))


def _role(client, driver: NegotiationDriver) -> Role:
    """Map a client back to its role for speaker attribution."""
    return Role.COP if client is driver.cop else Role.THIEF


def write_negotiation_md(session, out_dir: Path, match_id: str) -> Path:
    """Write the full natural-language negotiation dialogue to Markdown."""
    out = Path(out_dir) / match_id
    out.mkdir(parents=True, exist_ok=True)
    lines = [f"# Negotiation — `{match_id}`", ""]
    lines += [f"- **{m.sender}**: {m.text}" for m in session.mailbox]
    path = out / "negotiation.md"
    path.write_text("\n".join(lines) + "\n")
    return path
