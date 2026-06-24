"""Cop MCP server entry point (HTTP, token-guarded). Thin — delegates to factory.

Run with: ``uv run python -m robocop_mcp.mcp.cop_server``
"""

from __future__ import annotations

from ..constants import Role
from .server_app import run_server


def main() -> None:  # pragma: no cover - network entry point
    """Start the Cop server on its configured port (default 8001)."""
    run_server(Role.COP)


if __name__ == "__main__":  # pragma: no cover
    main()
