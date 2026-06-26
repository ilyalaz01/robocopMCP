"""Tests for interop translation (coords, directions, phrasing, parsing)."""

from __future__ import annotations

from robocop_mcp.constants import Direction
from robocop_mcp.interop.translation import OpponentProfile, Translator


def test_coord_roundtrip() -> None:
    t = Translator()
    assert t.cell_to_coord(0, 0) == "a1"  # bottom-left
    assert t.cell_to_coord(4, 4) == "e5"  # top-right
    assert t.coord_to_cell("c3") == (2, 2)
    assert t.coord_to_cell("E5") == (4, 4)


def test_phrase_move_outgoing() -> None:
    t = Translator()
    assert t.phrase_move(Direction.NE) == "I move up-right diagonal."
    assert t.phrase_move(Direction.N, (2, 3)) == "I move up to c4."


def test_parse_longest_direction_match() -> None:
    t = Translator()
    # "up-right diagonal" must win over the substring "up"/"right".
    assert t.parse_action("I move up-right diagonal.")["direction"] is Direction.NE
    assert t.parse_action("I move up.")["direction"] is Direction.N
    assert t.parse_action("I move down-left diagonal to a1.")["direction"] is Direction.SW


def test_parse_opponent_short_and_full_diagonals() -> None:
    """vm__fabi omits the 'diagonal' token; both short + full forms must parse right."""
    t = Translator()
    cases = {
        # cardinals
        "I move up.": Direction.N, "I move down.": Direction.S,
        "I move right.": Direction.E, "I move left.": Direction.W,
        # their SHORT diagonals (no 'diagonal' word) — must NOT collapse to a cardinal
        "I move up-right.": Direction.NE, "I move right-down.": Direction.SE,
        "I move down-left.": Direction.SW, "I move left-up.": Direction.NW,
        # the full phrases still work
        "I move up-right diagonal to b4.": Direction.NE,
        "I move right-down diagonal to c2.": Direction.SE,
        "I move down-left diagonal.": Direction.SW,
        "I move left-up diagonal.": Direction.NW,
    }
    for msg, expected in cases.items():
        assert t.parse_action(msg)["direction"] is expected, msg


def test_parse_block_loss_unclear() -> None:
    t = Translator()
    assert t.parse_action("I place a block.")["type"] == "block"
    assert t.parse_action("I've lost the game.")["type"] == "loss"
    assert t.parse_action("hmm, somewhere over there")["type"] == "unclear"


def test_parse_coordinate_non_authoritative() -> None:
    t = Translator()
    parsed = t.parse_action("I move up to c4.")  # direction authoritative, coord logged only
    assert parsed["direction"] is Direction.N
    assert parsed["coordinate"] == "c4"


def test_all_eight_directions_roundtrip() -> None:
    t = Translator()
    for d in [Direction.N, Direction.NE, Direction.E, Direction.SE,
              Direction.S, Direction.SW, Direction.W, Direction.NW]:
        assert t.parse_action(t.phrase_move(d))["direction"] is d


def test_custom_profile_phrasing() -> None:
    profile = OpponentProfile(move_template="Moving {word} now!")
    t = Translator(profile)
    assert t.phrase_move(Direction.E) == "Moving right now!"
    assert t.parse_action("Moving right now!")["direction"] is Direction.E
