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

# The ONLY negotiable parameters and their valid domains (ADR-0003 / SHARED_RULES).
# Agents may never invent rules outside this set (no time limits, head starts, etc.).
_MAX_BARRIERS_RANGE = (3, 8)
_MAX_MOVES_CHOICES = (25, 30)


def valid_rules(rules: dict) -> dict:
    """Filter + clamp a proposed ruleset to the negotiable domain.

    Unknown keys are dropped; ``max_barriers`` is clamped to 3–8 and
    ``max_moves`` snapped to {25, 30}. This is what stops the agents agreeing to
    anything undefined.
    """
    out: dict = {}
    if "max_barriers" in rules:
        lo, hi = _MAX_BARRIERS_RANGE
        out["max_barriers"] = max(lo, min(hi, int(rules["max_barriers"])))
    if "max_moves" in rules:
        mm = int(rules["max_moves"])
        out["max_moves"] = mm if mm in _MAX_MOVES_CHOICES else _MAX_MOVES_CHOICES[0]
    return out


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

    async def negotiate(self, proposal: dict, responder_stance: str, max_rounds: int,
                        target: dict | None = None) -> dict:
        """Negotiate within the valid domain; ``responder_stance`` is 'agree'/'counter'.

        ``target`` (the bonus profile's converged values) forces the final agreed
        ruleset so two engines stay identical — the dialogue still happens, it
        just lands there. Returns ``{agreed_rules, confirmed, rounds, conceded}``.
        """
        proposal = valid_rules(proposal)
        base = int(proposal.get("max_barriers", 5))
        await self._propose(self.cop, proposal, "propose its preferred ruleset")
        agreed, conceded, rounds = proposal, False, 0

        for r in range(max_rounds):
            rounds = r + 1
            if responder_stance == "agree":
                if r == 0 and max_rounds > 1:  # one flavour counter so logs aren't sterile
                    counter = valid_rules({"max_barriers": base + 1, "max_moves": 25})
                    await self._respond(self.thief, False, counter, "playfully ask for more barriers")
                    await self._propose(self.cop, proposal, "hold firm and explain the balance")
                    continue
                agreed = await self._respond(self.thief, True, {}, "accept the fair proposal")
                break
            counter = valid_rules({"max_barriers": base + 1 + r, "max_moves": 25})
            await self._respond(self.thief, False, counter, "counter within the agreed range")
            if r == max_rounds - 1:
                agreed = await self._respond(self.cop, True, {}, "concede gracefully and accept")
                conceded = True
            else:
                await self._propose(self.cop, proposal, "argue briefly for its ruleset")

        if target is not None:  # converge on the inter-team agreed values (bonus)
            agreed = valid_rules(target)
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
