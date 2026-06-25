"""MatchSession — interop match state for one opponent (pre-game → play → report).

Holds the agreed ruleset, team ordering, commit-reveal nonces, the current
sub-game (an :class:`InteropGame`/:class:`PlayerAgent`), and accumulated results.
The MCP tool service (:mod:`peer_tools`) is a thin token-guarded shell over this.
"""

from __future__ import annotations

from ..constants import Role
from ..domain.models import Position
from .capability_handshake import role_for, team_order
from .commit_reveal import derive_seed, generate_nonce, seed_to_positions, verify
from .game_adapter import build_rules
from .hashing import hash_payload, ruleset_hash
from .peer_agent import PlayerAgent
from .translation import OpponentProfile, Translator


class MatchSession:
    """Authoritative-for-our-side state of one interop match."""

    def __init__(self, team_name: str, grid: tuple[int, int] = (5, 5),
                 max_rounds: int = 25, max_barriers: int = 5) -> None:
        self.our_team = team_name
        self.ruleset_hash = ruleset_hash()
        self.profile = OpponentProfile()
        self.agent = PlayerAgent(team_name, Translator(self.profile))
        self.rules = build_rules(grid[0], grid[1], max_rounds, max_barriers)
        self.opponent_team: str | None = None
        self.team_a: str | None = None
        self.ruleset_accepted = False
        self.integrity_confirmed = False
        self.our_nonces: dict[int, str] = {}
        self.opp_commitments: dict[int, str] = {}
        self.opp_nonces: dict[int, str] = {}
        self.results: list[dict] = []
        # Final-report hash exchange (interop finalize is never auto-send).
        self.final_hash: str | None = None
        self.opponent_report_hash: str | None = None

    def set_opponent(self, team_name: str) -> None:
        """Record the opponent team and compute deterministic A/B ordering."""
        self.opponent_team = team_name
        self.team_a, _ = team_order(self.our_team, team_name)

    def accept_ruleset(self, name: str, rhash: str) -> bool:
        """Accept iff the opponent's ruleset name + hash exactly match ours."""
        self.ruleset_accepted = name == "cop-robber-grid-v1" and rhash == self.ruleset_hash
        return self.ruleset_accepted

    def our_commitment(self, sub_game_index: int):
        """Generate our nonce for a sub-game and return its public commitment."""
        from .commit_reveal import commitment
        self.our_nonces[sub_game_index] = generate_nonce()
        return commitment(self.our_nonces[sub_game_index])

    def reveal_ok(self, sub_game_index: int, nonce: str) -> bool:
        """Verify the opponent's revealed nonce against its earlier commitment."""
        ok = verify(nonce, self.opp_commitments.get(sub_game_index, ""))
        if ok:
            self.opp_nonces[sub_game_index] = nonce
        return ok

    def start_positions(self, sub_game_index: int) -> tuple[Position, Position]:
        """Derive (Cop, Robber) start cells from both nonces (commit-reveal).

        Nonces are ordered Team A then Team B (bit-exact: ``nonce_A`` is the
        lexicographically smaller team's), so both sides derive the same seed.
        """
        from .capability_handshake import normalize_team
        we_are_a = normalize_team(self.our_team) == normalize_team(self.team_a)
        ours, opp = self.our_nonces[sub_game_index], self.opp_nonces[sub_game_index]
        nonce_a, nonce_b = (ours, opp) if we_are_a else (opp, ours)
        seed = derive_seed(nonce_a, nonce_b, sub_game_index, self.ruleset_hash)
        return seed_to_positions(seed, self.rules.grid_width, self.rules.grid_height)

    def our_role(self, sub_game_index: int) -> Role:
        """Our assigned role for the sub-game (deterministic from team names)."""
        return role_for(sub_game_index, self.our_team, self.team_a)

    def sub_game_result(self, index: int, terminal_code: str, winner: str,
                        cop_score: int, robber_score: int) -> dict:
        """Build the per-sub-game result object + its canonical hash."""
        body = {"sub_game_index": index, "terminal_reason": terminal_code,
                "winner_role": winner, "scores": {"cop": cop_score, "robber": robber_score}}
        result = {**body, "log_hash": hash_payload(body)}
        self.results.append(result)
        return result
