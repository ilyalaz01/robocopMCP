"""Thin CLI — delegates to the SDK only (rubric §3.1: zero logic here).

Expanded in Phase 3 once the orchestrator exists. Tonight it exposes version
and config-validation so ``uv run robocop`` is wired end-to-end.
"""

from __future__ import annotations

import argparse

from . import __version__
from .shared.config import ConfigManager


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``robocop`` console script."""
    parser = argparse.ArgumentParser(prog="robocop", description="robocopMCP CLI")
    parser.add_argument("--version", action="version", version=f"robocopMCP {__version__}")
    parser.add_argument("--check-config", action="store_true", help="Validate config files")
    args = parser.parse_args(argv)

    if args.check_config:
        cfg = ConfigManager()
        cfg.game(), cfg.rate_limits(), cfg.logging()
        print(f"config OK (version {cfg.game()['version']})")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
