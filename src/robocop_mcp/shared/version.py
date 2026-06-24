"""Single source of truth for the code version (rubric §7.1).

The application validates that loaded config files declare a compatible
version (see :mod:`robocop_mcp.shared.config`). Bump this on meaningful
changes; the config ``"version"`` keys are bumped in lockstep.
"""

__version__ = "1.00"

# Config files declaring a version outside this set are rejected at load time.
# WHY a set, not a single string: lets us accept several historical configs
# during a migration window without code changes.
COMPATIBLE_CONFIG_VERSIONS = frozenset({"1.00"})
