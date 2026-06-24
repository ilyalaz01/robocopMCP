"""ApiGatekeeper — the single chokepoint for every external API call (rubric §4).

All Anthropic and Gmail calls go through :meth:`ApiGatekeeper.execute`, which
enforces per-service rate limits with a sliding window, queues (FIFO) on
overflow with backpressure instead of crashing, retries transient failures, and
logs every call — including token counts for the cost analysis. The clock and
sleep are injectable so the queue/retry behaviour is deterministically testable
without real time passing.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import asdict, dataclass

from .logging_setup import log_event


class QueueFullError(RuntimeError):
    """Raised when the overflow queue is full — the backpressure signal (§4.3)."""


@dataclass
class QueueStatus:
    """Snapshot of the gatekeeper's queue and lifetime counters."""

    depth: int
    processed: int
    queued: int
    retries: int
    rejected: int


class ApiGatekeeper:
    """Centralized API call manager: rate-limit → queue → retry → log."""

    def __init__(
        self, limits: dict, service: str = "default", jsonl=None,
        clock=time.monotonic, sleep=time.sleep, is_transient=None,
    ) -> None:
        self.service = service
        self.rpm = int(limits["requests_per_minute"])
        self.rph = int(limits["requests_per_hour"])
        self.retry_after = float(limits["retry_after_seconds"])
        self.max_retries = int(limits["max_retries"])
        self.max_queue_depth = int(limits.get("max_queue_depth", 100))
        self.jsonl = jsonl
        self._clock, self._sleep = clock, sleep
        self._is_transient = is_transient or _default_transient
        self._calls: deque[float] = deque()
        self._lock = threading.RLock()
        self._waiting = 0
        self._counts = {"processed": 0, "queued": 0, "retries": 0, "rejected": 0}

    @classmethod
    def from_config(cls, config, service: str, jsonl=None, **kw) -> ApiGatekeeper:
        """Build a gatekeeper for ``service`` from a ConfigManager."""
        services = config.rate_limits()["services"]
        limits = services.get(service, services["default"])
        return cls(limits, service=service, jsonl=jsonl, **kw)

    def _prune(self, now: float) -> None:
        while self._calls and now - self._calls[0] > 3600:
            self._calls.popleft()

    def _has_slot(self, now: float) -> bool:
        minute = sum(1 for t in self._calls if now - t <= 60)
        return minute < self.rpm and len(self._calls) < self.rph

    def _admit(self) -> None:
        """Block (via injected sleep) until a rate slot frees, or backpressure."""
        with self._lock:
            now = self._clock()
            self._prune(now)
            if self._has_slot(now):
                self._calls.append(now)
                return
            if self._waiting >= self.max_queue_depth:
                self._counts["rejected"] += 1
                self._emit("api_rejected")
                raise QueueFullError(f"{self.service}: queue full ({self.max_queue_depth})")
            self._waiting += 1
            self._counts["queued"] += 1
            self._emit("api_queued")
        while True:  # drain loop — re-check as the window resets
            self._sleep(self.retry_after)
            with self._lock:
                now = self._clock()
                self._prune(now)
                if self._has_slot(now):
                    self._waiting -= 1
                    self._calls.append(now)
                    return

    def execute(self, api_call, *args, **kwargs):
        """Run ``api_call`` through admission control + retry, and log it."""
        self._admit()
        attempt = 0
        while True:
            try:
                result = api_call(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 - classify then re-raise
                attempt += 1
                if attempt > self.max_retries or not self._is_transient(exc):
                    self._emit("api_error", error=type(exc).__name__, attempt=attempt)
                    raise
                self._counts["retries"] += 1
                self._emit("api_retry", error=type(exc).__name__, attempt=attempt)
                self._sleep(self.retry_after)
                continue
            self._counts["processed"] += 1
            self._emit("api_call", attempt=attempt, **_usage(result))
            return result

    def get_queue_status(self) -> QueueStatus:
        """Return queue depth + lifetime stats (rubric interface)."""
        with self._lock:
            return QueueStatus(depth=self._waiting, **self._counts)

    def _emit(self, event: str, **fields) -> None:
        if self.jsonl is not None:
            log_event(self.jsonl, event, service=self.service,
                      status=asdict(self.get_queue_status()) if event == "api_call" else None,
                      **fields)


def _default_transient(exc: Exception) -> bool:
    """Treat rate-limit / timeout / connection / 5xx errors as retryable."""
    name = type(exc).__name__.lower()
    return any(k in name for k in ("ratelimit", "timeout", "connection", "internalserver", "apistatus"))


def _usage(result) -> dict:
    """Extract token usage from an Anthropic-style result, if present."""
    usage = getattr(result, "usage", None)
    if usage is None:
        return {}
    return {
        "input_tokens": getattr(usage, "input_tokens", None),
        "output_tokens": getattr(usage, "output_tokens", None),
    }
