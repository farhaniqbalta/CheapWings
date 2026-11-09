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
    live_data: bool = False
    permitted_to_aggregate: bool = True
    can_cache: bool = True
    attribution_required: bool = False
    retention_seconds: int | None = None
    usage_policy_reviewed_on: str | None = None

    def __post_init__(self):
        if self.concurrency < 1 or self.minimum_interval_seconds < 0:
            raise ValueError("Provider concurrency must be positive and interval nonnegative")

    @property
    def unavailable_reason(self):
        if not self.permitted_to_aggregate:
            return 'terms_not_approved for configured scope'
        if not self.enabled:
            return self.disabled_reason or "disabled by configuration"
        if not self.provider.capabilities.detailed_search:
            return "detailed search unsupported"
        return None


def default_registry(settings=None):
    from importlib.util import find_spec

    from cheapwings.config import Settings
    from cheapwings.providers.skiplagged import SkiplaggedProvider
    from cheapwings.providers.swoop import SwoopProvider

    settings = settings or Settings.from_env()
    if settings.enabled_providers == ('fake',):
        return [Registration(FakeProvider())]
    registrations = []
    for provider, dependencies in ((SkiplaggedProvider(), ('mcp','httpx2')),
                                    (SwoopProvider(), ('swoop','airportsdata'))):
        selected = provider.provider_id in settings.enabled_providers
        missing = [name for name in dependencies if find_spec(name) is None]
        reason = ('disabled by configuration' if not selected else
                  'install backend[live]; missing: ' + ', '.join(missing) if missing else None)
        registrations.append(Registration(provider, enabled=selected and not missing,
            disabled_reason=reason, concurrency=1, minimum_interval_seconds=15,
            live_data=True, permitted_to_aggregate=settings.use_scope == 'personal',
            can_cache=True, attribution_required=True,
            retention_seconds=settings.live_retention_seconds, usage_policy_reviewed_on='2026-11-09'))
    return registrations
