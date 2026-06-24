"""Thief MCP server entry point (HTTP, token-guarded). Thin — delegates to factory.

Run with: ``uv run python -m robocop_mcp.mcp.thief_server``
"""

from __future__ import annotations

from ..constants import Role
from .server_app import run_server


def main() -> None:  # pragma: no cover - network entry point
    """Start the Thief server on its configured port (default 8002)."""
    run_server(Role.THIEF)


if __name__ == "__main__":  # pragma: no cover
    main()
