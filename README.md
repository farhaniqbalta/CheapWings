# CheapWings

Personal-use, flexible-date, one-way flight comparison with a Python 3.12+
backend and React/TypeScript web client. Durable SQLite jobs, a separate worker,
REST v1, and Skiplagged/swoop adapters are implemented. Development defaults to
**synthetic fake fares**; live providers are opt-in for accepted personal use.
Native SwiftUI iOS is the next phase and requires full Xcode.

[WORK_LOG.md](WORK_LOG.md) is the source of truth for phase status, decisions,
validation evidence, and the exact next task. Provider observations are in
[provider feasibility evidence](WORK_LOG.md#provider-feasibility-evidence).

## Local setup

Run from the repository root. Existing `.venv/` is the backend environment.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e './backend[dev]'
cp .env.example .env
set -a
source .env
set +a
alembic -c backend/alembic.ini upgrade head
uvicorn cheapwings.main:app --host "$API_BIND_HOST" --port "$API_BIND_PORT"
```

In a second terminal, from the same root and with the same environment:

```sh
source .venv/bin/activate
set -a
source .env
set +a
python -m cheapwings.worker
```

Exactly one worker owns a database, enforced with a POSIX advisory file lock.
The API does not execute provider work. Both commands reject missing/outdated
migrations; neither silently creates tables. Use a local disk database, not a
network filesystem. Relative database URLs resolve from the working directory.

## Run the web client

With the API and worker running, open a third terminal. Node 22.18+ is required
(the existing project environment uses Node 26):

```sh
cd apps/web
npm ci
cp .env.example .env
npm run dev -- --host localhost --port 5173 --strictPort
```

Open `http://localhost:5173`. `apps/web/.env` uses
`VITE_API_BASE_URL=http://127.0.0.1:8000`; the default backend CORS allowlist permits
`http://localhost:5173`. If changing the browser origin, update
`CORS_ALLOWED_ORIGINS` in the backend environment and restart the API.

The URL retains `?job=...` for recovery after refresh. Safe results and
**Lowest advertised** remain separate views; pagination uses **Load more results**.
Cancellation preserves discovered offers. Origin-local flight times retain their
source offsets; unresolved timezones are labeled unknown.

For a private authenticated backend, expand **Private server access** and enter
the owner token at runtime. The token stays in tab memory, is never added to the
URL or browser storage, and must be re-entered after refresh. Do not put tokens
or upstream credentials in `VITE_*` variables: these become public build assets.
Use HTTPS for remote private access; no public deployment is configured.

## Optional real personal-use searches

P3 adapters passed an actual low-volume canary in the prior session. To opt in,
install the pinned extras and change the backend `.env` in both service shells:

```sh
.venv/bin/python -m pip install -e './backend[dev,live]'
```

```dotenv
ENABLED_PROVIDERS=skiplagged,swoop
CHEAPWINGS_USE_SCOPE=personal
JOB_REPRICE_BUDGET=20
LIVE_RETENTION_SECONDS=3600
```

Restart the API and worker after sourcing the updated environment. Fake and live
providers cannot be mixed in one configuration. Registry metadata exposes missing
dependencies, disabled sources, and terms restrictions. Live results expire after
the configured job retention window; expired result requests return `410`.
Skiplagged prices remain indicative; swoop's unknown hidden-city risk excludes
its offers from the safe ranking. **Lowest advertised** exposes those candidates
with their evidence and warnings. No provider price is guaranteed bookable.

## Try the API

Interactive contract: `http://127.0.0.1:8000/api/v1/docs`.
Choose future dates; the sample below is a synthetic fixture, not a live fare.

```sh
curl -sS -X POST http://127.0.0.1:8000/api/v1/searches \
  -H 'Content-Type: application/json' \
  -d '{"origins":["MEL"],"destinations":["CGK","DPS","SUB"],"departure_date_from":"2026-12-12","departure_date_through":"2026-12-20","display_currency":"IDR"}'
```

The `202` response has `job_id` and `job_status_url`. Poll the status URL every
2–5 seconds. Read `{job_status_url}/results?sort=best_checked&limit=50` or use
`sort=lowest_advertised`. Send `POST {job_status_url}/cancel` to stop work and
preserve completed fares. `GET /api/v1/capabilities` lists current adapter flags,
disablement reasons and server limits. No provider secrets/selectors are public.

Results group complete matching itineraries and preserve distinct seller
quotes. `ranked_quote_id` identifies the offer determining each group's sort
position; alternative offers retain their own eligibility/risk labels. Prices
are decimal **strings**, never JSON money numbers. Provider failure is distinct
from successful empty results. Coverage is unique route/date combinations,
separate from provider work counts; inventory completeness remains unknown.

Cursors freeze the quote set at the first page. Use the same job and sort for
subsequent pages. To see fares found after that snapshot, start again without
a cursor. Results expose `as_of`; job status is current. An empty best-checked
view does not prove no flights: inspect coverage and the advertised view.

## Worker behavior

- Each claim increments an auditable attempt and creates a fenced lease.
  Result inserts and terminal success share one transaction. Per-job/provider
  source quote keys prevent duplicates. A failed transaction leaves the lease
  recoverable and no partial fares.
- Global provider concurrency and spacing apply across jobs. Provider cooldowns
  persist in SQLite, including `Retry-After`. Transient errors get up to three
  attempts with capped exponential backoff; auth/schema errors terminate.
  Adapters may raise normalized `ProviderFailure(code, retry_after_seconds)`.
- Stale running work is reclaimed only after its lease expires; recovery runs
  every tick and at startup. Defaults: 30s provider timeout, 40s lease, 30-minute
  job budget (including queue time/restarts). Budget exhaustion is a visible
  failure, not empty success. Completed work never reruns automatically.
- Cancellation invalidates outstanding leases immediately; late results are
  ignored. In-process provider slots remain occupied until calls finish.
  Stopping the worker leaves leases for restart. Closing a client has no effect.
- The swoop adapter uses a bounded one-thread executor: cancelling an await cannot force-kill a blocking thread. An adapter
  needs its own network timeout; do not release its actual execution slot early.
- Registry changes produce explicit skipped entries for removed/disabled
  adapters; unknown provider IDs are rejected.

## Access and budgets

Without `CHEAPWINGS_OWNER_TOKEN`, only direct loopback clients and localhost
Host headers are accepted. For LAN, proxy, or private-tunnel use, set a random
owner token of at least 32 characters **in both shells**, use HTTPS at the
boundary, and send `Authorization: Bearer <token>` on capabilities/search/job/
results/cancel requests. All jobs belong to this one owner; there is no multi-user
service or public deployment. Do not log or commit the token. Set
`API_BIND_HOST` consistently with Uvicorn's `--host`; request checks also reject
external unauthenticated clients if the CLI binding was accidentally overridden.
Only the documented CORS origins are allowed. Health and OpenAPI carry no secrets.

Job creation is atomically limited to 2 active jobs and 20 jobs/hour for the
single owner (including cancelled jobs); excess returns `429`. A job is limited
to 120 combinations, and request validation forbids caller-controlled caps,
unsupported passenger/cabin/currency settings, and expired departure dates.
Airport codes currently validate by shape; an airport reference and origin-local
expiry validation need to accompany later real-provider integration. P2 expiry
uses the server calendar date. Current display currencies: IDR/USD/AUD/JPY.

No raw provider payloads or passenger PII are stored. Live normalized fares, FX
evidence, selectors, and revisions expire after the configured retention window
and are purged independently per source observation by the worker or results request.
Expiry does not shorten the job execution budget or remove another source's fresh
quotes. Results return HTTP 200 with `expired_observations` metadata cards after
restricted fare details are removed; no old price or expired booking link remains.
`next_expiry_at` and `server_time` let clients refresh even completed searches.
The legacy job-level `data_expires_at` is nullable for new searches; migration
preserves existing cutoffs. Indefinite archival of live prices is not enabled:
only permitted search/coverage metadata survives expiry. Fake jobs persist
until the owner removes the local DB with both services stopped.
Back up SQLite with its backup API or with both services stopped; copying only
the main file while WAL writes are active is unsafe. No upstream network calls or paid services
are required in fake mode.

## Validation and contract

```sh
.venv/bin/python -m pytest backend/tests -q
.venv/bin/python -m cheapwings.cli_demo
.venv/bin/python scripts/export_openapi.py
# Opt-in local process acceptance; needs permission to bind localhost sockets:
.venv/bin/python scripts/p2_smoke.py
```

[contracts/openapi.yaml](contracts/openapi.yaml) is generated JSON (valid YAML
1.2), avoiding a YAML runtime dependency. Tests compare it to the served schema
and roundtrip typed responses. Integration tests use temporary migrated SQLite
DBs and fake providers, including failures, leases, restart, cancellation,
transaction rollback, auth, quotas and pagination. No default test calls an
external provider. P2 process smoke and the P3 production-adapter canary passed
in the prior session; their evidence is recorded in WORK_LOG.md. Current managed
sandbox restrictions can still prevent starting servers or browsers.

Web validation (from `apps/web`): `npm test` and `npm run build`. Browser
regressions: `npm run test:browser` after Chromium is installed with
`npx playwright install chromium`. This suite uses synthetic intercepted responses
and makes no provider calls. The four core scenarios and 39 state/viewport cases passed after the carrier/airport-change fix; restricted sessions may require permission to start Chromium.

Full Xcode is still required for P5; command-line tools alone cannot build SwiftUI.
See [the phase checkpoints](docs/06_IMPLEMENTATION_CHECKPOINTS.md) for remaining work.

## P4.5 web refinement

The owner accepted the integrated web design, which is merged into main.
[WORK_LOG.md](WORK_LOG.md) records the design decisions, component map,
validation and current next task. Integrated synthetic screenshots remain in
[docs/design/p45-qa](docs/design/p45-qa/); completed handoff prompts are retired.
Native SwiftUI P5 remains a separate requirement and needs full Xcode.

## Observation cache and optional OctoTrip source

Set `SEARCH_CACHE_ENABLED=true` in the API and worker environment to reuse
complete source observations for repeated or overlapping route/date searches.
Default freshness is 1,200 seconds, bounded by original retention and each
provider's cache policy. Incomplete, unknown-completeness and unpriced responses
are not reused. `SEARCH_CACHE_MAX_ENTRIES` and `SEARCH_CACHE_MAX_BYTES` bound
storage. Apply Alembic migrations before restarting both processes.

Cache hits preserve original prices, FX evidence, observation times and expiry;
they do not become verified prices. Cached copies omit private repricing handles.
Matching in-flight requests share a durable fetch, with independent job IDs and
cancellation. `MAX_HOURLY_SEARCH_REQUESTS` and `MAX_ACTIVE_SEARCH_REQUESTS` also
bound cached/coalesced requests; existing provider-work job limits still apply to
new work. Force-refresh requests respect those limits and source pacing.

The backend accepts optional `provider_ids` (distinct enabled source IDs) and
`cache_mode` (`prefer_cache` or `refresh`) on POST `/api/v1/searches`. Omitting
provider IDs uses the current configured sources; the resolved set is persisted.
Source selection remains backend-only. The web shows cache/shared provenance and
provides **Run fresh search**, which creates a new job with the same selections.

OctoTrip is available for owner-approved personal use by adding `octotrip` to
`ENABLED_PROVIDERS`, for example `skiplagged,swoop,octotrip`. Install backend live
extras for the airport timezone reference. It provides an indicative shortlist
with source-supplied sellers and baggage statements; hidden-city/self-transfer,
fare products and mandatory costs remain unknown. Nearby-airport candidates are
excluded from explicit-airport searches. Endpoint times use the validated airport
reference; complete operating-carrier/segment identity is not inferred.
OctoTrip caching and exact repricing remain disabled. Its conservative 900-second
result lifecycle also caps a mixed-source job's expiry/budget; select the existing
two sources through the API when a longer matrix needs their usual lifecycle.
Software defaults remain fake-only; source/accuracy evidence and owner approvals
are recorded solely in WORK_LOG.md.
