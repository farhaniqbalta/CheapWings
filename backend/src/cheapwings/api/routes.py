import secrets
from contextlib import asynccontextmanager
from dataclasses import asdict
from ipaddress import ip_address
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError
from sqlalchemy import text

from cheapwings.application import contracts as dto
from cheapwings.application.search_service import (
    instant,
    results_projection,
    status_projection,
)
from cheapwings.config import Settings
from cheapwings.engine.expansion import expand_routes_and_dates
from cheapwings.providers.registry import default_registry
from cheapwings.storage.db import database, require_current_schema
from cheapwings.storage.repository import CapacityExceeded, Repository
from cheapwings.storage.verification import ResultsExpired


def create_app(settings=None, registry=None, engine=None):
    settings = settings or Settings.from_env()
    registry = registry if registry is not None else default_registry(settings)
    if len({r.provider.provider_id for r in registry}) != len(registry):
        raise ValueError("Duplicate provider IDs")
    owns_engine = engine is None
    engine = engine if engine is not None else database(settings.database_url)
    repo = Repository(
        engine,
        cache_enabled=settings.search_cache_enabled,
        cache_ttl_seconds=settings.search_cache_ttl_seconds,
        cache_max_entries=settings.search_cache_max_entries,
        cache_max_bytes=settings.search_cache_max_bytes,
    )

    @asynccontextmanager
    async def lifespan(app):
        require_current_schema(engine)
        yield
        if owns_engine:
            engine.dispose()

    app = FastAPI(
        title="CheapWings API",
        version="1.0.0",
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.repository = repo
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.middleware("http")
    async def local_boundary(request: Request, call_next):
        if not settings.owner_token:
            try:
                local = request.client is not None and ip_address(request.client.host).is_loopback
            except ValueError:
                local = False
            if not local or request.url.hostname not in ("localhost", "127.0.0.1", "::1"):
                return JSONResponse(
                    {"detail": "Remote access requires configured owner auth"}, status_code=403
                )
        return await call_next(request)

    bearer = HTTPBearer(auto_error=False)

    def authorized(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
        if settings.owner_token and (
            credentials is None
            or not secrets.compare_digest(credentials.credentials, settings.owner_token)
        ):
            raise HTTPException(
                401, "Owner bearer token required", headers={"WWW-Authenticate": "Bearer"}
            )

    @app.exception_handler(ResultsExpired)
    async def results_expired(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=410)

    @app.exception_handler(KeyError)
    async def not_found(request, exc):
        return JSONResponse({"detail": "Search not found"}, status_code=404)

    router = APIRouter(prefix="/api/v1")

    @router.get("/health", response_model=dto.Health)
    def health():
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
        return dto.Health()

    secured = APIRouter(dependencies=[Depends(authorized)])

    @secured.get("/capabilities", response_model=dto.Capabilities)
    def capabilities():
        return dto.Capabilities(
            search_cache_enabled=settings.search_cache_enabled,
            search_cache_ttl_seconds=settings.search_cache_ttl_seconds,
            max_hourly_requests=settings.max_hourly_requests,
            providers=[
                dto.ProviderCapability(
                    provider_id=r.provider.provider_id,
                    enabled=r.unavailable_reason is None,
                    disabled_reason=r.unavailable_reason,
                    **asdict(r.provider.capabilities),
                    permitted_to_aggregate=r.permitted_to_aggregate,
                    can_cache=r.can_cache,
                    attribution_required=r.attribution_required,
                    retention_seconds=r.retention_seconds,
                    usage_policy_reviewed_on=r.usage_policy_reviewed_on,
                )
                for r in registry
            ],
            supported_currencies=["IDR", "USD", "AUD", "JPY"],
            max_route_date_combinations=settings.max_combinations,
            max_active_jobs=settings.max_active_jobs,
            max_hourly_jobs=settings.max_hourly_jobs,
            synthetic_mode=not any(r.live_data for r in registry if r.unavailable_reason is None),
        )

    @secured.post(
        "/searches",
        response_model=dto.Created,
        status_code=202,
        responses={
            422: {"description": "Invalid query"},
            429: {"description": "Creation budget exceeded"},
        },
    )
    def create_search(payload: dto.SearchRequest, response: Response):
        try:
            query = payload.to_domain(settings.max_combinations)
        except (ValueError, ValidationError) as exc:
            raise HTTPException(422, str(exc)) from None
        selected = registry
        if payload.provider_ids is not None:
            ids = payload.provider_ids
            available = {r.provider.provider_id for r in registry if r.unavailable_reason is None}
            if len(set(ids)) != len(ids) or not set(ids) <= available:
                raise HTTPException(422, "Choose distinct enabled and approved provider IDs")
            selected = [r for r in registry if r.provider.provider_id in ids]
        try:
            job = repo.create_job(
                query,
                selected,
                max_active=settings.max_active_jobs,
                max_hourly=settings.max_hourly_jobs,
                budget_seconds=settings.job_budget_seconds,
                cache_mode=payload.cache_mode,
                max_requests=settings.max_hourly_requests,
                max_active_requests=settings.max_active_requests,
                reprice_budget=settings.reprice_budget,
                retention_seconds=None,  # each observation has its own source cutoff
            )
        except CapacityExceeded as exc:
            raise HTTPException(429, str(exc)) from None
        url = f"/api/v1/searches/{job.id}"
        response.headers["Location"] = url
        return dto.Created(
            job_id=job.id,
            status=job.status,
            created_at=instant(job.created_at),
            total_route_date_combinations=len(expand_routes_and_dates(query)),
            enabled_detailed_providers=[
                r.provider.provider_id for r in selected if r.unavailable_reason is None
            ],
            job_status_url=url,
        )

    @secured.get("/searches/{job_id}", response_model=dto.Job)
    def get_job(job_id: str):
        return status_projection(repo, job_id)

    @secured.get("/searches/{job_id}/results", response_model=dto.Results)
    def get_results(
        job_id: str,
        sort: dto.Sort = "best_checked",
        cursor: str | None = Query(default=None, max_length=2048),
        limit: int = Query(default=50, ge=1, le=100),
    ):
        try:
            return results_projection(repo, job_id, sort, cursor, limit)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from None

    @secured.post("/searches/{job_id}/cancel", response_model=dto.Job)
    def cancel(job_id: str):
        repo.cancel(job_id)
        return status_projection(repo, job_id)

    router.include_router(secured)
    app.include_router(router)
    return app
