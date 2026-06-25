"""Orchestrator — the MCP client that drives negotiation + play (SPEC §5).

Parameterized by two targets (``cop_target``, ``thief_target``) that are either
FastMCP server objects (in-memory, for tests/local) or HTTP URLs (for real runs
and the inter-team bonus). It owns the per-sub-game and per-series loops and the
technical-loss/void re-run handling; the actual decisions come from an injected
``decider`` (heuristic now, LLM in Phase 5).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastmcp import Client

from ..constants import Outcome, Role
from ..domain.models import MatchRules, SubGameResult
from ..domain.rules import accumulate
from ..domain.starts import generate_starts
from ..mcp.session import SessionRegistry
from ..shared.logging_setup import log_event
from .turn_loop import Decider, _call, default_decider, play_turn


@dataclass
class SeriesResult:
    """Outcome of a full 6-sub-game series."""

    match_id: str
    sub_games: list[SubGameResult]
    totals: dict[str, int]


class Orchestrator:
    """Drives sub-games and series over the two MCP servers."""

    def __init__(
        self, cop_target: Any, thief_target: Any, token: str,
        registry: SessionRegistry, jsonl, max_void_retries: int = 3,
    ) -> None:
        self.cop_target = cop_target
        self.thief_target = thief_target
        self.token = token
        self.registry = registry
        self.jsonl = jsonl
        self.max_void_retries = max_void_retries

    async def run_series(
        self, rules: MatchRules, decider: Decider = default_decider, match_id: str = "local",
    ) -> SeriesResult:
        """Play ``rules.num_games`` valid sub-games and accumulate the scores."""
        starts = generate_starts(rules, rules.num_games)
        async with Client(self.cop_target) as cop_c, Client(self.thief_target) as thief_c:
            clients = {Role.COP: cop_c, Role.THIEF: thief_c}
            results: list[SubGameResult] = []
            attempt = 0
            while len(results) < rules.num_games:
                start = starts[len(results)]
                res = await self._run_subgame(len(results), rules, clients, decider, match_id, start)
                if res.void:
                    attempt += 1
                    log_event(self.jsonl, "subgame_void", match_id=match_id, attempt=attempt)
                    if attempt > self.max_void_retries:
                        results.append(res)  # give up re-running; record the void
                    continue
                results.append(res)
            totals = accumulate([(r.cop_score, r.thief_score) for r in results])
            log_event(self.jsonl, "series_end", match_id=match_id, totals=totals)
            return SeriesResult(match_id, results, totals)

    async def _run_subgame(
        self, index: int, rules: MatchRules, clients: dict, decider: Decider,
        match_id: str, start: tuple,
    ) -> SubGameResult:
        """Run one pursuit round to completion (or void) over the MCP tools."""
        session_id = f"{match_id}-sg{index}"
        session = self.registry.create(session_id, rules)
        engine = session.engine
        # Per-sub-game start positions (ADR-0003) so the 6 games differ.
        engine.reset(cop=start[0], thief=start[1])
        log_event(self.jsonl, "subgame_start", match_id=match_id, index=index,
                  cop=engine.state.cop.as_tuple(), thief=engine.state.thief.as_tuple())

        for _ in range(rules.max_moves + 2):
            digest = (await _call(clients[Role.COP], "match_digest",
                                  session_id=session_id, token=self.token))["digest"]
            # Log the full authoritative state each ply — feeds the board renders.
            log_event(self.jsonl, "state", session_id=session_id, **digest)
            if digest["outcome"] != Outcome.ONGOING.value:
                break
            turn = Role(digest["turn"])
            res = await play_turn(clients[turn], turn, self.token, session_id, self.jsonl, decider)
            if not res.get("ok"):
                # An unrecoverable turn (e.g. a fully trapped Thief) → void + re-run.
                engine.state.outcome = Outcome.VOID
                break

        result = engine.result(index)
        log_event(self.jsonl, "subgame_end", match_id=match_id, index=index,
                  outcome=result.outcome.value, moves=result.moves,
                  cop_score=result.cop_score, thief_score=result.thief_score)
        return result
