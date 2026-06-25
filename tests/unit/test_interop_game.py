"""Tests for InteropGame — interop rules over our engine (blocks-both, codes)."""

from __future__ import annotations

from robocop_mcp.constants import Direction, Role
from robocop_mcp.domain.models import Position
from robocop_mcp.interop.game_adapter import InteropGame, build_rules


def _game() -> InteropGame:
    return InteropGame(build_rules(5, 5, 25, 5))


def test_build_rules_doubles_rounds_to_plies() -> None:
    assert build_rules(5, 5, 25, 5).max_moves == 50  # 25 full rounds = 50 plies


def test_blocks_impassable_to_both_players() -> None:
    g = _game()
    g.start(cop=Position(2, 2), robber=Position(0, 0))
    g.engine.state.barriers.add(Position(2, 3))  # north of cop
    # Unlike our solo engine (blocks only the thief), here the Cop is blocked too.
    assert Direction.N not in g.legal_move_dirs(Role.COP)


def test_cop_capture_terminal() -> None:
    g = _game()
    g.start(cop=Position(2, 2), robber=Position(3, 2))
    g.apply_move(Role.THIEF, Direction.N)   # robber flees to (3,3)
    code = g.apply_move(Role.COP, Direction.NE)  # cop steps onto (3,3)
    assert code == "cop_capture"


def test_robber_moved_into_cop_terminal() -> None:
    g = _game()
    g.start(cop=Position(2, 2), robber=Position(2, 3))
    code = g.apply_move(Role.THIEF, Direction.S)  # robber steps onto the cop
    assert code == "robber_moved_into_cop"


def test_illegal_move_off_board() -> None:
    g = _game()
    g.start(cop=Position(0, 0), robber=Position(4, 4))
    g.apply_move(Role.THIEF, Direction.SW)  # robber legal move first
    code = g.apply_move(Role.COP, Direction.S)  # cop off the board
    assert code == "cop_illegal_action"


def test_block_budget_and_on_blocked_cell() -> None:
    g = _game()
    g.start(cop=Position(2, 2), robber=Position(4, 4))
    g.apply_move(Role.THIEF, Direction.SW)
    assert g.can_block(Role.COP)
    g.apply_block(Role.COP)               # block placed on (2,2); cop stays
    g.apply_move(Role.THIEF, Direction.NW)
    assert not g.can_block(Role.COP)      # cannot block while standing on a blocked cell


def test_no_legal_action_codes() -> None:
    g = _game()
    g.start(cop=Position(2, 2), robber=Position(0, 0))
    assert g.no_legal_action_code(Role.THIEF) == "robber_no_legal_move"
    assert g.no_legal_action_code(Role.COP) == "cop_no_legal_action"
