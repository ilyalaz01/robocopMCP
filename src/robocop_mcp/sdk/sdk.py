"""MarlSDK — the single entry point to all business logic (rubric §3.1).

Every consumer (CLI, notebook, future REST) goes through this class and never
reaches into internal modules. It assembles the two MCP servers over a shared
session registry and exposes high-level operations; methods are added phase by
phase (play now; training, negotiation, reporting later).
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastmcp import Client

from ..constants import Role
from ..domain.models import MatchRules, Position
from ..learning.q_learning import QTable
from ..mcp.server_app import make_server, resolve_token
from ..mcp.session import SessionRegistry
from ..orchestrator.negotiation import (
    NegotiationDriver,
    template_speaker,
    write_negotiation_md,
)
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

    def negotiate(self, stance: str = "agree", match_id: str = "local",
                  speaker=None, apply: bool = True) -> dict:
        """Run pre-game rule negotiation; optionally adopt the agreed ruleset."""
        session_id = f"{match_id}-neg"
        self.registry.create(session_id, self.rules)
        proposal = {"max_barriers": self.cfg.get("max_barriers", default=5),
                    "grid_size": list(self.cfg.get("grid_size", default=[5, 5]))}
        max_rounds = self.cfg.get("negotiation", "max_rounds", default=6)
        result = asyncio.run(self._negotiate(session_id, proposal, stance, max_rounds, speaker))
        write_negotiation_md(self.registry.get(session_id), self.cfg.root / "results", match_id)
        if apply and result["agreed_rules"]:
            self.rules = self._apply_agreement(result["agreed_rules"])
        _LOG.info("Negotiation %s: agreed=%s confirmed=%s conceded=%s", match_id,
                  result["agreed_rules"], result["confirmed"], result["conceded"])
        return result

    async def _negotiate(self, session_id, proposal, stance, max_rounds, speaker):
        async with Client(self.cop_server) as cop_c, Client(self.thief_server) as thief_c:
            driver = NegotiationDriver(cop_c, thief_c, self.token, session_id, self.jsonl,
                                       speaker or template_speaker)
            return await driver.negotiate(proposal, stance, max_rounds)

    def _apply_agreement(self, agreed: dict) -> MatchRules:
        """Translate an agreed-rules dict into an effective MatchRules override."""
        changes: dict = {}
        if "max_barriers" in agreed:
            changes["max_barriers"] = int(agreed["max_barriers"])
        if agreed.get("grid_size"):
            w, h = (int(v) for v in agreed["grid_size"][:2])
            changes.update(grid_width=w, grid_height=h,
                           cop_start=Position(0, 0), thief_start=Position(w - 1, h - 1))
        return self.rules.with_overrides(**changes)

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
