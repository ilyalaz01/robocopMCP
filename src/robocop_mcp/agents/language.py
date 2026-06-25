"""Natural-language layer — message generation + interpretation (SPEC §8).

The LLM (Haiku) writes each agent's free-text message and reads the opponent's
to infer a coarse belief about its position. Every model call goes through the
:class:`ApiGatekeeper`. Each call has a timeout and a deterministic templated
fallback, so an unattended run never hangs and every fallback is logged.
"""

from __future__ import annotations

from ..agents.persona import INTERPRETER_PROMPT, NEGOTIATOR_PERSONA, persona_for
from ..constants import Role
from ..shared.logging_setup import log_event


def _extract_text(resp) -> str:
    """Pull the text out of an Anthropic-style response (or a plain string)."""
    content = getattr(resp, "content", None)
    if content:
        block = content[0]
        return getattr(block, "text", str(block)).strip()
    return str(resp).strip()


def _build_context(role: Role, obs: dict, opponent_msgs: list, suggestion: str | None) -> str:
    """Compose the user prompt describing the agent's current situation."""
    last = opponent_msgs[-1]["text"] if opponent_msgs else "(silence)"
    seen = obs.get("opponent_pos")
    sight = "you can SEE the opponent nearby" if seen else "the opponent is OUT OF SIGHT"
    intent = suggestion or "hold"
    return (
        f"You are the {role.value}. Turn {obs.get('move_count', '?')}. {sight}. "
        f"Opponent's last words: \"{last}\". You intend to move {intent}. "
        "Write your short in-character message now."
    )


class LanguageEngine:
    """Generates and interprets natural-language messages via Haiku."""

    def __init__(self, gatekeeper, create_fn, model: str, max_tokens: int,
                 temperature: float, timeout: int, jsonl=None, deception: bool = True) -> None:
        self.gk = gatekeeper
        self.create = create_fn
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.jsonl = jsonl
        # When False (bonus open-information profile), the truthful persona is used.
        self.deception = deception

    def _complete(self, system: str, user: str) -> str | None:
        """One guarded LLM completion; returns text or ``None`` on any failure."""
        try:
            resp = self.gk.execute(
                self.create, model=self.model, system=system, max_tokens=self.max_tokens,
                temperature=self.temperature, timeout=self.timeout,
                messages=[{"role": "user", "content": user}],
            )
            return _extract_text(resp)
        except Exception as exc:  # noqa: BLE001 - fall back, never propagate to the loop
            if self.jsonl is not None:
                log_event(self.jsonl, "llm_fallback", error=type(exc).__name__)
            return None

    def message(self, role: Role, obs: dict, opponent_msgs: list, suggestion: str | None) -> str:
        """Generate the agent's message, falling back to a template on failure."""
        system = persona_for(role, self.deception)
        text = self._complete(system, _build_context(role, obs, opponent_msgs, suggestion))
        if text:
            return text
        intent = suggestion or "hold"
        verb = "closing in" if role is Role.COP else "slipping away"
        return f"[{role.value}] {verb} ({intent})."

    def negotiation_line(self, role: Role, intent: str, detail: str) -> str:
        """One short negotiation utterance (propose/argue/accept/concede/confirm)."""
        user = (f"You are the {role.value}. You want to {intent}. Context: {detail}. "
                "Say it in one short, polite sentence.")
        return self._complete(NEGOTIATOR_PERSONA, user) or f"[{role.value}] {intent}: {detail}"

    def interpret(self, role: Role, message: str) -> str:
        """Infer a coarse directional belief about the opponent from a message."""
        text = self._complete(INTERPRETER_PROMPT, f"Reader is the {role.value}. Opponent said: {message}")
        token = (text or "UNKNOWN").strip().upper().split()
        return token[0] if token else "UNKNOWN"
