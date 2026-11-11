"""Provider feedback parsing and a single-owner HTTP start gate."""

import asyncio
import math
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from time import monotonic

from cheapwings.domain.evidence import ProviderFailure


def retry_after(value, *, default=60, now=None):
    try:
        seconds = int(value)
        if seconds >= 0:
            return seconds
    except (TypeError, ValueError):
        pass
    try:
        deadline = parsedate_to_datetime(value)
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=UTC)
        return max(0, math.ceil((deadline - (now or datetime.now(UTC))).total_seconds()))
    except (TypeError, ValueError, OverflowError):
        return default


def provider_failure(exc):
    """Inspect nested MCP exception groups without exposing exception text."""
    if isinstance(exc, BaseExceptionGroup):
        failures = [provider_failure(e) for e in exc.exceptions]
        failures = [f for f in failures if f is not None]
        if failures:
            limited = [f for f in failures if f.code == "http_rate_limited"]
            return max(limited, key=lambda f: f.retry_after_seconds) if limited else failures[0]
        return None
    if isinstance(exc, ProviderFailure):
        return exc
    if isinstance(exc, TimeoutError) or any(
        cls.__name__ == "TimeoutException" and cls.__module__.split(".")[0] in ("httpx", "httpx2")
        for cls in type(exc).__mro__
    ):
        return ProviderFailure("network_timeout")
    response = getattr(exc, "response", None)
    status = getattr(response, "status_code", None)
    if status == 429:
        return ProviderFailure(
            "http_rate_limited", retry_after(response.headers.get("Retry-After"))
        )
    if status in (401, 403):
        return ProviderFailure("auth_denied")
    return None


class HttpStartGate:
    """Shared by every session of a provider in the one locked worker process."""

    def __init__(self, interval=1.10):
        self.interval = interval
        self.next_start = 0
        self.cooldown_until = 0
        self.lock = asyncio.Lock()

    def defer(self, seconds):
        self.cooldown_until = max(self.cooldown_until, monotonic() + seconds)

    def check_cooldown(self):
        remaining = self.cooldown_until - monotonic()
        if remaining > 0:
            raise ProviderFailure("http_rate_limited", math.ceil(remaining))

    async def wait(self):
        async with self.lock:
            self.check_cooldown()
            await asyncio.sleep(max(0, self.next_start - monotonic()))
            self.check_cooldown()
            self.next_start = monotonic() + self.interval
