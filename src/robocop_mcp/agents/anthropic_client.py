"""Anthropic client wiring — the only place that imports the live SDK.

Kept isolated (and excluded from coverage) so the rest of the codebase depends
on a plain ``create_fn`` callable that is trivially mockable in tests. The API
key is loaded process-locally from ``.env`` via python-dotenv — never exported
into the shell, never committed (rubric §6.4).
"""

from __future__ import annotations

import os

from ..shared.gatekeeper import ApiGatekeeper
from .language import LanguageEngine


def build_create_fn():  # pragma: no cover - exercised only in live runs
    """Return a callable that performs one Anthropic ``messages.create`` call."""
    from anthropic import Anthropic
    from dotenv import load_dotenv

    load_dotenv()
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def create(model, system, messages, max_tokens, temperature, timeout):
        return client.messages.create(
            model=model, system=system, messages=messages,
            max_tokens=max_tokens, temperature=temperature, timeout=timeout,
        )

    return create


def build_language_engine(config, jsonl, create_fn=None) -> LanguageEngine:  # pragma: no cover
    """Assemble a gatekeeper-guarded :class:`LanguageEngine` from config."""
    llm = config.game()["llm"]
    gatekeeper = ApiGatekeeper.from_config(config, "anthropic", jsonl)
    return LanguageEngine(
        gatekeeper, create_fn or build_create_fn(), llm["model"], llm["max_tokens"],
        llm["temperature"], llm["timeout_seconds"], jsonl,
    )
