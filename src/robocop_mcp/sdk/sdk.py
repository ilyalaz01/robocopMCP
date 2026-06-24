"""MarlSDK — the single entry point to all business logic (rubric §3.1).

Every consumer (CLI, notebook, future REST) goes through this class and never
reaches into internal modules. It assembles the two MCP servers over a shared
session registry and exposes high-level operations; methods are added phase by
phase (play now; training, negotiation, reporting later).
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from ..constants import Role
from ..domain.models import MatchRules
from ..learning.q_learning import QTable
from ..mcp.server_app import make_server, resolve_token
from ..mcp.session import SessionRegistry
from ..orchestrator.orchestrator import Orchestrator, SeriesResult
from ..orchestrator.turn_loop import Decider, default_decider, make_llm_decider
from ..shared.config import ConfigManager
from ..shared.logging_setup import get_logger, setup_logging

_LOG = get_logger("robocop.sdk")


class MarlSDK:
    """Façade over the pursuit-game pipeline.

    Setup:  config (ConfigManager | None), token (str | None — defaults to the
            revocable token from env/config).
    """

    def __init__(self, config: ConfigManager | None = None, token: str | None = None) -> None:
        self.cfg = config or ConfigManager()
        self.jsonl = setup_logging(self.cfg)
        self.token = token or resolve_token(self.cfg)
        self.rules = MatchRules.from_config(self.cfg.game())
        self.registry = SessionRegistry()
        self.qtables = self._load_qtables()
        # In-memory servers share one registry (ADR-0002); HTTP runs use the launcher.
        self.cop_server = make_server(
            Role.COP, self.token, self.registry, self.cfg, self.qtables.get(Role.COP)
        )
        self.thief_server = make_server(
            Role.THIEF, self.token, self.registry, self.cfg, self.qtables.get(Role.THIEF)
        )
        self.orchestrator = Orchestrator(
            self.cop_server, self.thief_server, self.token, self.registry, self.jsonl
        )

    def _load_qtables(self) -> dict:
        """Load trained Q-tables from ``results/qtables`` if present (else heuristic)."""
        out: dict = {}
        base = self.cfg.root / "results" / "qtables"
        for role, name in ((Role.COP, "qtable_cop.json"), (Role.THIEF, "qtable_thief.json")):
            path = Path(base) / name
            if path.is_file():
                out[role] = QTable.load(path)
        return out

    def build_llm_decider(self, create_fn=None) -> Decider:  # pragma: no cover - live LLM
        """Build the Haiku-backed decider (message = LLM, move = Q-suggestion)."""
        from ..agents.anthropic_client import build_language_engine

        engine = build_language_engine(self.cfg, self.jsonl, create_fn)
        return make_llm_decider(engine, self.jsonl)

    def run_series(
        self, rules: MatchRules | None = None, decider: Decider = default_decider,
        match_id: str = "local",
    ) -> SeriesResult:
        """Play a full series and return the accumulated result (sync wrapper)."""
        rules = rules or self.rules
        _LOG.info("Starting series %s (%d sub-games)", match_id, rules.num_games)
        result = asyncio.run(self.orchestrator.run_series(rules, decider, match_id))
        _LOG.info("Series %s totals: %s", match_id, result.totals)
        return result

    def run_sub_game(self, rules: MatchRules | None = None, index: int = 0) -> SeriesResult:
        """Play a single sub-game (a one-game series) — convenience for demos/tests."""
        rules = (rules or self.rules).with_overrides(num_games=1)
        return self.run_series(rules, match_id=f"single{index}")
