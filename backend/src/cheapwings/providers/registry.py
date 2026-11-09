"""Adapter registration and policy gating; callers never branch on provider IDs."""

from dataclasses import dataclass

from cheapwings.providers.base import SearchProvider
from cheapwings.providers.fake import FakeProvider


@dataclass(frozen=True)
class Registration:
    provider: SearchProvider
    enabled: bool = True
    disabled_reason: str | None = None
    concurrency: int = 1
    minimum_interval_seconds: float = 1

    def __post_init__(self):
        if self.concurrency < 1 or self.minimum_interval_seconds < 0:
            raise ValueError("Provider concurrency must be positive and interval nonnegative")

    @property
    def unavailable_reason(self):
        if not self.enabled:
            return self.disabled_reason or "disabled by configuration"
        if not self.provider.capabilities.detailed_search:
            return "detailed search unsupported"
        return None


def default_registry():
    return [Registration(FakeProvider())]
