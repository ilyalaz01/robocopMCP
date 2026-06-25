"""PlayerAgent — a role-flexible correspondence-game player (assignment §3).

Holds its OWN inferred state (an :class:`InteropGame` over our GameEngine),
chooses only legal actions, phrases them in the opponent's natural language, and
parses+validates the opponent's messages against its own state. The same agent
plays Cop or Robber. ``play_sub_game`` runs two agents to a terminal result over
the message protocol — the local self-play proof (no central referee, mocked LLM).
"""

from __future__ import annotations

from ..constants import Role
from ..domain.models import MatchRules, Position
from .game_adapter import STR_FROM_ROLE, InteropGame
from .translation import Translator


def default_policy(game: InteropGame, role: Role):
    """Deterministic heuristic: Cop chases, Robber evades; Cop blocks if boxed in."""
    legal = game.legal_move_dirs(role)
    if not legal:
        return ("block", None) if game.can_block(role) else ("loss", None)
    own = game._own(role)
    opp = game.engine.state.thief if role is Role.COP else game.engine.state.cop
    board = game.engine.board

    def dist(direction):
        return board.step(own, direction).chebyshev(opp)

    best = min(legal, key=dist) if role is Role.COP else max(legal, key=dist)
    return ("move", best)


class PlayerAgent:
    """One reusable agent that can play either role (assignment §3.1)."""

    def __init__(self, team_name: str, translator: Translator | None = None,
                 policy=default_policy, token: str = "interop-token") -> None:
        self.team_name = team_name
        self.translator = translator or Translator()
        self.policy = policy
        self.token = token
        self.role: Role | None = None
        self.game: InteropGame | None = None
        self.log: list[dict] = []

    def start_sub_game(self, role: Role, cop: Position, robber: Position,
                       rules: MatchRules) -> None:
        """Initialise this agent's own inferred game for a sub-game."""
        self.role = role
        self.game = InteropGame(rules)
        self.game.start(cop, robber)
        self.log = []

    def act(self) -> tuple[str, str | None]:
        """Choose + apply my action on my own state; return (message, terminal)."""
        kind, direction = self.policy(self.game, self.role)
        if kind == "move":
            dest = self.game.engine.board.step(self.game._own(self.role), direction)
            message = self.translator.phrase_move(direction, dest.as_tuple())
            code = self.game.apply_move(self.role, direction)
        elif kind == "block":
            message = self.translator.phrase_block()
            code = self.game.apply_block(self.role)
        else:
            message = self.translator.phrase_loss()
            code = self.game.admit_loss(self.role)
        self.log.append({"actor": STR_FROM_ROLE[self.role], "message": message, "kind": kind})
        return message, code

    def observe(self, message: str, actor_role: Role) -> dict:
        """Parse + apply the opponent's message to my own state (one retry handled upstream)."""
        parsed = self.translator.parse_action(message)
        if parsed["type"] == "unclear":
            return {"parsed": parsed, "ack": False, "code": None}
        if parsed["type"] == "move":
            code = self.game.apply_move(actor_role, parsed["direction"])
        elif parsed["type"] == "block":
            code = self.game.apply_block(actor_role)
        else:
            code = self.game.admit_loss(actor_role)
        self.log.append({"actor": STR_FROM_ROLE[actor_role], "message": message, "observed": True})
        return {"parsed": parsed, "ack": True, "code": code}


def _other(role: Role) -> Role:
    return Role.THIEF if role is Role.COP else Role.COP


def play_sub_game(cop_agent: PlayerAgent, rob_agent: PlayerAgent, cop: Position,
                  robber: Position, rules: MatchRules) -> str | None:
    """Drive two agents through one sub-game over the message protocol."""
    cop_agent.start_sub_game(Role.COP, cop, robber, rules)
    rob_agent.start_sub_game(Role.THIEF, cop, robber, rules)
    agents = {Role.COP: cop_agent, Role.THIEF: rob_agent}
    code: str | None = None
    for _ in range(rules.max_moves + 2):
        if cop_agent.game.engine.state.is_terminal():
            break
        actor_role = cop_agent.game.engine.state.turn
        actor, receiver = agents[actor_role], agents[_other(actor_role)]
        if not actor.game.has_legal_action(actor_role):
            code = actor.game.no_legal_action_code(actor_role)
            receiver.observe(actor.translator.phrase_loss(), actor_role)
            break
        message, code = actor.act()
        receiver.observe(message, actor_role)
        if code:
            break
    return code
