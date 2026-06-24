"""Tabular Q-learning — Bellman update + epsilon-greedy policy (SPEC §9).

State is the clamped relative displacement ``(dx, dy)`` from the agent to its
target (the opponent), which keeps the table small and board-size agnostic.
Actions are the 8 moves (plus ``PLACE_BARRIER`` for the Cop). The table is
JSON-serialisable so trained policies are human-inspectable for the report.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ..constants import MOVE_DIRECTIONS, PLACE_BARRIER, Role
from ..domain.models import Position


def action_space(role: Role) -> list[str]:
    """The ordered action names for ``role`` (Cop also may place a barrier)."""
    moves = [d.value for d in MOVE_DIRECTIONS]
    return [*moves, PLACE_BARRIER] if role is Role.COP else moves


def encode_state(own: Position, target: Position, clamp: int = 4) -> tuple[int, int]:
    """Clamped relative displacement target−own → a small discrete state key."""
    dx = max(-clamp, min(clamp, target.x - own.x))
    dy = max(-clamp, min(clamp, target.y - own.y))
    return (dx, dy)


class QTable:
    """A tabular action-value function with the standard Q-learning update."""

    def __init__(
        self, actions: list[str], alpha: float = 0.1, gamma: float = 0.9,
        epsilon: float = 0.2, epsilon_decay: float = 0.999, min_epsilon: float = 0.01,
        rng: np.random.Generator | None = None,
    ) -> None:
        self.actions = actions
        self.alpha, self.gamma = alpha, gamma
        self.epsilon, self.epsilon_decay, self.min_epsilon = epsilon, epsilon_decay, min_epsilon
        self.rng = rng or np.random.default_rng()
        self.q: dict[tuple[int, int], np.ndarray] = {}

    def row(self, state: tuple[int, int]) -> np.ndarray:
        """Return (creating if needed) the action-value row for ``state``."""
        if state not in self.q:
            self.q[state] = np.zeros(len(self.actions), dtype=float)
        return self.q[state]

    def select(self, state: tuple[int, int], legal: list[int], explore: bool = True) -> int:
        """Epsilon-greedy action index restricted to ``legal`` actions."""
        if not legal:
            return 0
        if explore and self.rng.random() < self.epsilon:
            return int(self.rng.choice(legal))
        row = self.row(state)
        # Argmax over legal actions only (mask the rest with -inf).
        masked = np.full_like(row, -np.inf)
        masked[legal] = row[legal]
        return int(np.argmax(masked))

    def update(self, s: tuple[int, int], a: int, reward: float, s_next: tuple[int, int]) -> None:
        """Bellman update: Q(s,a) ← Q(s,a) + α·[r + γ·max Q(s',·) − Q(s,a)]."""
        row = self.row(s)
        best_next = float(np.max(self.row(s_next)))
        row[a] += self.alpha * (reward + self.gamma * best_next - row[a])

    def decay(self) -> None:
        """Decay exploration toward ``min_epsilon`` after each episode."""
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)

    def save(self, path: Path) -> None:
        """Persist the table to JSON (states stringified as ``"dx,dy"``)."""
        payload = {
            "actions": self.actions,
            "params": {"alpha": self.alpha, "gamma": self.gamma, "epsilon": self.epsilon},
            "q": {f"{s[0]},{s[1]}": row.tolist() for s, row in self.q.items()},
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(payload, indent=2))

    @classmethod
    def load(cls, path: Path) -> QTable:
        """Load a table previously written by :meth:`save`."""
        data = json.loads(Path(path).read_text())
        table = cls(data["actions"])
        for key, row in data["q"].items():
            dx, dy = (int(v) for v in key.split(","))
            table.q[(dx, dy)] = np.array(row, dtype=float)
        return table
