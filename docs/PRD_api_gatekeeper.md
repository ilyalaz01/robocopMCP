# PRD — API Gatekeeper

**Version 1.00.** Rubric §4. All external calls go through it; nothing bypasses it.

## Background
A single chokepoint for **every** external API call (Anthropic, Gmail). It enforces rate
limits before each call, queues on overflow (never drops/crashes), retries transient
failures, and logs every call (including token counts for cost analysis).

## Interface
```python
class ApiGatekeeper:
    def __init__(self, config: RateLimitConfig): ...
    def execute(self, api_call, *args, **kwargs): ...   # limit → queue → retry → log
    def get_queue_status(self) -> QueueStatus: ...      # depth + stats
```

## Rate limiting (from `config/rate_limits.json`)
Per-service `requests_per_minute`, `requests_per_hour`, `concurrent_max`,
`retry_after_seconds`, `max_retries`, `max_queue_depth`. A sliding-window counter gates
admission; when the window is full, the call goes to a **FIFO queue**.

## Queue management (§4.3)
FIFO; bounded by `max_queue_depth`; **backpressure** signal when full; **drain** as windows
reset. Overflow beyond the bound raises a typed `QueueFullError` (caller decides) — it does
not crash the process.

## Retry
Transient failures (timeouts, 5xx, 429) retried up to `max_retries` with
`retry_after_seconds` backoff; permanent failures surface immediately.

## Logging
Each call logs: service, latency, attempt count, outcome, and **input/output tokens** (when
the wrapped result exposes usage) → feeds the token-cost notebook.

## Edge cases / tests
Under-limit pass-through; over-limit → queue → drain; queue overflow → backpressure;
transient error → retry then success; permanent error → surfaced; token accounting.

## Success criteria
No call path bypasses the gatekeeper; queue-overflow + retry covered by tests.
