"""Explicit environment configuration; .env is optional shell input, never auto-loaded."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./data/cheapwings.db"
    bind_host: str = "127.0.0.1"
    owner_token: str | None = None
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)
    max_combinations: int = 120
    max_active_jobs: int = 2
    max_hourly_jobs: int = 20
    job_budget_seconds: int = 1800
    call_timeout_seconds: int = 30
    lease_seconds: int = 40
    max_attempts: int = 3
    enabled_providers: tuple[str, ...] = ('fake',)
    use_scope: str = 'personal'
    reprice_budget: int = 20
    live_retention_seconds: int = 3600

    def __post_init__(self):
        if not self.enabled_providers or set(self.enabled_providers) - {'fake','skiplagged','swoop'}:
            raise ValueError('Unknown or empty provider configuration')
        if 'fake' in self.enabled_providers and len(self.enabled_providers) != 1:
            raise ValueError('Synthetic and live providers cannot share a search')
        if self.reprice_budget < 0 or not 60 <= self.live_retention_seconds <= 3600:
            raise ValueError('Invalid verification budget or live retention (60..3600 seconds)')
        if self.bind_host not in ("127.0.0.1", "::1", "localhost") and not self.owner_token:
            raise ValueError("Non-loopback binding requires CHEAPWINGS_OWNER_TOKEN")
        if self.owner_token is not None and len(self.owner_token) < 32:
            raise ValueError("Owner token must contain at least 32 characters")
        for value in (
            self.max_combinations,
            self.max_active_jobs,
            self.max_hourly_jobs,
            self.job_budget_seconds,
            self.call_timeout_seconds,
            self.max_attempts,
        ):
            if value < 1:
                raise ValueError("Budgets must be positive")
        if self.lease_seconds <= self.call_timeout_seconds:
            raise ValueError("Lease must exceed provider timeout")

    @classmethod
    def from_env(cls):
        return cls(
            enabled_providers=tuple(dict.fromkeys(filter(None, os.getenv('ENABLED_PROVIDERS','fake').split(',')))),
            use_scope=os.getenv('CHEAPWINGS_USE_SCOPE','personal'),
            reprice_budget=int(os.getenv('JOB_REPRICE_BUDGET','20')),
            live_retention_seconds=int(os.getenv('LIVE_RETENTION_SECONDS','3600')),
            database_url=os.getenv("DATABASE_URL", cls.database_url),
            bind_host=os.getenv("API_BIND_HOST", cls.bind_host),
            owner_token=os.getenv("CHEAPWINGS_OWNER_TOKEN") or None,
            cors_origins=tuple(
                filter(None, os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(","))
            ),
            max_combinations=int(os.getenv("MAX_ROUTE_DATE_COMBINATIONS", "120")),
            max_active_jobs=int(os.getenv("GLOBAL_MAX_ACTIVE_SEARCH_JOBS", "2")),
            max_hourly_jobs=int(os.getenv("MAX_HOURLY_SEARCH_JOBS", "20")),
            job_budget_seconds=int(os.getenv("JOB_BUDGET_SECONDS", "1800")),
            call_timeout_seconds=int(os.getenv("PROVIDER_TIMEOUT_SECONDS", "30")),
            lease_seconds=int(os.getenv("WORK_LEASE_SECONDS", "40")),
            max_attempts=int(os.getenv("MAX_WORK_ATTEMPTS", "3")),
        )
