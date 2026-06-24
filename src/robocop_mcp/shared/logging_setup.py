"""Structured logging — the project's #1 deliverable (SPEC §13).

Two sinks are produced for every run:
- a human-readable ``.log`` (and console) for quick reading, and
- a machine-readable ``.jsonl`` event stream (one JSON object per line) that
  the notebook and report builders mine for tokens, turns, and outcomes.

WHY a custom JSONL emitter rather than a logging Formatter: we want explicit,
typed event records (``log_event``) independent of Python's log levels, so the
analysis layer never has to parse free-form log strings.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import ConfigManager

_CONFIGURED = False


def setup_logging(config: ConfigManager | None = None) -> Path:
    """Configure root logging + ensure the JSONL event file exists.

    Returns the path to the JSONL event file so callers can pass it to
    :func:`log_event`. Idempotent: safe to call from every entry point.
    """
    global _CONFIGURED
    cfg = config or ConfigManager()
    log_cfg = cfg.logging()
    log_dir = cfg.root / log_cfg.get("log_dir", "logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = log_dir / log_cfg.get("jsonl_event_file", "events.jsonl")

    if not _CONFIGURED:
        level = getattr(logging, str(log_cfg.get("level", "INFO")).upper(), logging.INFO)
        handlers: list[logging.Handler] = [
            logging.FileHandler(log_dir / log_cfg.get("human_log_file", "robocop.log"))
        ]
        if log_cfg.get("console", True):
            handlers.append(logging.StreamHandler())
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
            handlers=handlers,
            force=True,
        )
        _CONFIGURED = True
    return jsonl_path


def _iso_now() -> str:
    """UTC ISO-8601 timestamp; stable, sortable, locale-independent."""
    return datetime.now(timezone.utc).isoformat()


def log_event(jsonl_path: Path, event: str, **fields: Any) -> dict[str, Any]:
    """Append one structured event to the JSONL stream and return the record.

    Every domain action (turn, move, message, api_call, capture, fallback,
    error) routes through here, giving the professor a complete, greppable
    audit trail without running the code.
    """
    record: dict[str, Any] = {"ts": _iso_now(), "mono": round(time.monotonic(), 6), "event": event}
    record.update(fields)
    Path(jsonl_path).parent.mkdir(parents=True, exist_ok=True)
    with open(jsonl_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    return record


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger (thin wrapper for import-site clarity)."""
    return logging.getLogger(name)
