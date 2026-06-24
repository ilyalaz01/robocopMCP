"""robocop_mcp — dual AI agent pursuit race over two natural-language MCP servers.

Public entry point is the SDK (:class:`robocop_mcp.sdk.sdk.MarlSDK`), per the
rubric's SDK-first architecture (§3.1). External consumers import from here and
never reach into internal modules.
"""

from __future__ import annotations

from .constants import Direction, Outcome, Role
from .shared.version import __version__

__all__ = ["__version__", "Role", "Outcome", "Direction"]
