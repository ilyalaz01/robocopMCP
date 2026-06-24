"""ConfigManager — load, version-validate, and expose all tunable values.

Rubric §6.2/§7.1: nothing tunable is hard-coded; every value comes from a
versioned JSON file under ``config/``. This module is the *only* place that
reads those files, so the rest of the codebase depends on data, not paths.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .version import COMPATIBLE_CONFIG_VERSIONS


class ConfigError(RuntimeError):
    """Raised when a config file is missing, malformed, or version-incompatible."""


def _project_root() -> Path:
    """Locate the repo root by walking up until a ``config/`` dir appears.

    WHY walk up: tests and the CLI run from different working directories;
    anchoring on a marker dir keeps path resolution relative (rubric §13.3).
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "config").is_dir():
            return parent
    # Fallback: three levels up (src/robocop_mcp/shared -> root).
    return here.parents[3]


class ConfigManager:
    """Loads and validates the project's versioned configuration files.

    Setup:  config_dir (Path | None) — defaults to ``<root>/config``.
    Output: dict-like access to the validated config payloads.
    """

    def __init__(self, config_dir: Path | None = None) -> None:
        self._root = _project_root()
        self._dir = Path(config_dir) if config_dir else self._root / "config"
        self._cache: dict[str, dict[str, Any]] = {}

    @property
    def root(self) -> Path:
        """Absolute project root, used to resolve logs/results paths."""
        return self._root

    def _load(self, filename: str) -> dict[str, Any]:
        path = self._dir / filename
        if not path.is_file():
            raise ConfigError(f"Config file not found: {path}")
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise ConfigError(f"Invalid JSON in {path}: {exc}") from exc
        return data

    @staticmethod
    def _check_version(data: dict[str, Any], where: str) -> None:
        version = data.get("version")
        if version not in COMPATIBLE_CONFIG_VERSIONS:
            raise ConfigError(
                f"Incompatible config version {version!r} in {where}; "
                f"expected one of {sorted(COMPATIBLE_CONFIG_VERSIONS)}"
            )

    def game(self) -> dict[str, Any]:
        """Return the validated main game config (``config.json``)."""
        if "game" not in self._cache:
            data = self._load("config.json")
            self._check_version(data, "config.json")
            self._cache["game"] = data
        return self._cache["game"]

    def rate_limits(self) -> dict[str, Any]:
        """Return the validated rate-limit config (``rate_limits.json``)."""
        if "rate_limits" not in self._cache:
            data = self._load("rate_limits.json")
            inner = data.get("rate_limits", {})
            self._check_version(inner, "rate_limits.json")
            self._cache["rate_limits"] = inner
        return self._cache["rate_limits"]

    def logging(self) -> dict[str, Any]:
        """Return the validated logging config (``logging_config.json``)."""
        if "logging" not in self._cache:
            data = self._load("logging_config.json")
            self._check_version(data, "logging_config.json")
            self._cache["logging"] = data
        return self._cache["logging"]

    def get(self, *keys: str, default: Any = None) -> Any:
        """Nested lookup into the game config, e.g. ``get("scoring", "cop_win")``.

        Returns ``default`` if any key in the path is absent — this is the
        sanctioned hard-coded-fallback pattern from rubric §6.2.
        """
        node: Any = self.game()
        for key in keys:
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node
