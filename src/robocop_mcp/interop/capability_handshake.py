"""Capability handshake — the generic adapter to ANY opponent (assignment §5.2).

At match start we exchange capabilities and build an :class:`OpponentProfile`. If
the opponent exposes ``get_capabilities`` we adapt to what it reports; if it does
not, we fall back to the opponent team's DOCUMENTED conventions (the defaults),
which is why it works out-of-the-box with them and adapts for everyone else. Also
holds the deterministic team-name role ordering (their §5.6).
"""

from __future__ import annotations

from ..constants import Direction, Role
from .constants import DIR_TO_WORD, RULESET_NAME
from .hashing import ruleset_hash
from .translation import OpponentProfile, default_profile

_DIR_ORDER = [Direction.N, Direction.NE, Direction.E, Direction.SE,
              Direction.S, Direction.SW, Direction.W, Direction.NW]


def our_capabilities(team_name: str, repo_url: str, mcp_urls: dict, students: list) -> dict:
    """The capability payload we advertise to the opponent (assignment §5.2)."""
    return {
        "team_name": team_name, "students": students, "repo_url": repo_url,
        "mcp_urls": mcp_urls, "ruleset_name": RULESET_NAME, "ruleset_hash": ruleset_hash(),
        "role_flexible": True, "timeout_seconds": 60,
        "invalid_action_retries": 1, "timeout_retries": 1,
        "action_vocabulary": [DIR_TO_WORD[d] for d in _DIR_ORDER],
        "coordinate_style": "chess_like", "randomness_protocol": "commit_reveal",
        "supports_email_report": True,
    }


def build_opponent_profile(capabilities: dict | None) -> OpponentProfile:
    """Build an OpponentProfile from reported capabilities, defaulting documented.

    Falls back entirely to the opponent team's documented conventions when the
    opponent does not implement ``get_capabilities`` (capabilities is ``None``).
    """
    profile = default_profile()
    if not capabilities:
        return profile
    vocab = capabilities.get("action_vocabulary")
    if isinstance(vocab, list) and len(vocab) == 8:  # adapt direction wording, by our order
        profile.dir_to_word = dict(zip(_DIR_ORDER, vocab, strict=True))
    profile.timeout_seconds = int(capabilities.get("timeout_seconds", profile.timeout_seconds))
    if capabilities.get("move_template"):
        profile.move_template = capabilities["move_template"]
    return profile


def normalize_team(name: str) -> str:
    """Trim + lowercase for lexicographic team ordering (their §5.6)."""
    return name.strip().lower()


def team_order(name_a: str, name_b: str) -> tuple[str, str]:
    """Return (Team A, Team B) by normalized lexicographic order (smaller = A)."""
    if normalize_team(name_a) == normalize_team(name_b):
        raise ValueError("identical normalized team names — use distinct display names")
    return (name_a, name_b) if normalize_team(name_a) < normalize_team(name_b) else (name_b, name_a)


def role_for(sub_game_index: int, our_team: str, team_a_name: str) -> Role:
    """Our role in sub-game ``sub_game_index`` (1-based): A=Cop for 1-3, else Robber."""
    we_are_a = normalize_team(our_team) == normalize_team(team_a_name)
    a_is_cop = sub_game_index <= 3
    if we_are_a:
        return Role.COP if a_is_cop else Role.THIEF
    return Role.THIEF if a_is_cop else Role.COP
