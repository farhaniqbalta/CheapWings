# CheapWings

Personal-use, flexible-date, one-way flight comparison with a Python 3.12+
backend and React/TypeScript web client. Durable SQLite jobs, a separate worker,
REST v1, and Skiplagged/swoop/OctoTrip/Fli adapters are implemented. Development defaults to
**synthetic fake fares**; live providers are opt-in for accepted personal use.
Native SwiftUI iOS remains planned and requires full Xcode.

[WORK_LOG.md](WORK_LOG.md) holds current status, approvals and the next task.
Detailed evidence is indexed in [docs/log/README.md](docs/log/README.md).
Provider observations are in
[provider feasibility evidence](docs/log/provider-feasibility-evidence.md).

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

## Smart location selection (P4.10)

Origin and destination accept airport codes/names, cities and countries using an
included offline catalog. **Specific Airports** is the default: a city/country
opens a browse filter; manually selected airport chips are the exact search scope.
**Major Airports** is opt-in and shows an explicit curated list before search.
Unmapped places require Specific selection. Switch back to Specific to retain
and narrow a Major list; entering Major with existing selections asks you to
clear them explicitly.

The preview excludes same-airport pairs and uses the backend's runtime limit
(default 120). Over-budget searches stay fully selected and cannot submit;
remove airports or shorten the dates. Provider work counts are upper-bound
estimates. Typing never invokes flight providers. Catalog membership does not
promise scheduled service, route support or fares.

Existing IATA-array callers remain supported. Optional typed Major metadata is
re-resolved and validated by the backend; `POST /api/v1/locations/resolve` offers
standalone authoritative resolution. [Catalog source, refresh procedure, API
contract, tests and limitations](docs/log/p4.10.md).

## Optional real personal-use searches

P3 adapters passed an actual low-volume canary in the prior session. To opt in,
install the pinned extras and change the backend `.env` in both service shells:

```sh
.venv/bin/python -m pip install -e './backend[dev,live]'
```

```dotenv
ENABLED_PROVIDERS=skiplagged,swoop,octotrip,fli
CHEAPWINGS_USE_SCOPE=personal
JOB_REPRICE_BUDGET=20
LIVE_RETENTION_SECONDS=3600
```

Restart the API and worker after sourcing the updated environment. Fake and live
providers cannot be mixed in one configuration. Registry metadata exposes missing
dependencies, disabled sources, and terms restrictions. Fare details expire per
source observation; results remain HTTP 200 with expired metadata, without old
prices or booking links. See [retention and budgets](#access-and-budgets).
Skiplagged prices remain indicative; swoop's unknown hidden-city risk excludes
its offers from the safe ranking. **Lowest advertised** exposes those candidates
with their evidence and warnings. No provider price is guaranteed bookable.

Current live limitation (2026-11-11): swoop's RPC transport returns upstream
errors in controlled checks. The adapter now reports these as failures and
invalidates earlier false-empty cache entries; live swoop fare retrieval is
not restored. Transport replacement is deferred beyond P4.9 scheduling work.
See the [diagnosis and phase handoff](docs/log/p4.9.md).

Fli is a fourth, independent scheduling option using Google's public search
page. Its current 0.10.0 source is pinned to commit
`881aee5ff4321e81ea2157cb44be94ce6a21dc1b` (PyPI's older 0.9.0 is not used),
with curl-cffi 0.17.0 and explicit HTTP/2. Installing the live extra requires
Git to fetch that commit. Set `FLI_INTERVAL_SECONDS=1` in both API/worker
environments.

Fli offers appear under **Lowest advertised** as indicative shopping quotes;
links open a Google Flights search, not a confirmed seller fare. Basic-economy
exclusion is rejected before any provider request. Baggage, fees and hidden-city
risk remain unknown; exact repricing is not advertised. Fli and swoop both use
Google Flights and do not constitute independent inventory confirmation.
[P4.11 measurements and limits](docs/log/p4.11.md).

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
- One asyncio queue owner admits eligible work fairly across providers and jobs
  from one shared global pool (default nine physical operations, 1..100). There
  is no per-provider concurrency ceiling: any provider may use idle global
  capacity. Start-to-start intervals decide when a provider may begin a request
  (defaults: Skiplagged 3s, swoop 0.1s, OctoTrip 5s, Fli 1s); cooldowns and
  Retry-After still apply. Providers have priority tiers (`<PROVIDER>_PRIORITY`,
  0 = highest; OctoTrip defaults to 1): a lower tier only gets a slot when no
  higher tier has eligible work, and cannot take the last `LOW_PRIORITY_HEADROOM`
  slots (default 2), so a later fast search never waits behind slow calls.
  A slow response adds no mandatory cooldown after
  completion. Live providers remain opt-in. Override `WORKER_MAX_IN_FLIGHT` and
  `<PROVIDER>_INTERVAL_SECONDS` in both shells (see `.env.example`).
  Transient errors get up to three
  attempts with capped exponential backoff; auth/schema errors terminate.
  Adapters may raise normalized `ProviderFailure(code, retry_after_seconds)`.
- Stale running work is reclaimed only after its lease expires; recovery runs
  at startup and at most 100ms between maintenance checks. Defaults: 30s provider timeout, 40s lease (OctoTrip:
  90s timeout and at least 100s lease), 30-minute
  job budget (including queue time/restarts). Budget exhaustion is a visible
  failure, not empty success. Completed work never reruns automatically.
- Cancellation invalidates outstanding leases immediately; late results are
  ignored. In-process provider slots remain occupied until calls finish.
  Stopping the worker leaves leases for restart. Closing a client has no effect.
- Blocking adapters use bounded executors as an adapter-intrinsic limit, not a
  scheduler policy: swoop keeps three threads (obsolete, pending replacement);
  Fli's threads spawn lazily up to the global pool size. Overflow is rejected
  instead of queued. Logical timeout/cancellation retains
  physical capacity until actual I/O ends. Graceful worker shutdown drains threads
  before releasing ownership; a permanently stuck thread requires process termination.
- OctoTrip shares one ≥1.10s HTTP-start gate across initialization and tool calls
  in every concurrent session. A 429 blocks unsent peer messages and persists the
  provider cooldown. HTTP Retry-After seconds and dates are supported; swoop's SDK
  omits response headers, so its rate-limit fallback remains 120 seconds.
- Registry changes produce explicit skipped entries for removed/disabled
  adapters; unknown provider IDs are rejected.

The P4.9 implementation keeps the durable queue, leases/fencing, retries,
shared cache operations and progressive result commits. Dispatch ordering is
persisted by an additive migration; stop old API/worker processes, run
`.venv/bin/alembic -c backend/alembic.ini upgrade head`, then restart both.
Migration downgrades preserve the earlier schema. The owner approved C3 settings;
P4.8 confirmed C3 overlap for Skiplagged and OctoTrip, but did not show a consistent
C3 speed advantage; swoop C3 still lacks live validation. See [WORK_LOG.md](WORK_LOG.md)
for measurements and limitations. No Rust or separate worker service is required.

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

Admission is atomic for the single owner: by default, at most 20 active search
requests and 100 requests/hour, including cache hits and shared operations.
Jobs reserving new upstream work also face limits of 2 active and 20/hour;
cancelled jobs still count toward hourly budgets. Excess returns `429`. A job is limited
to 120 combinations, and request validation forbids caller-controlled caps,
unsupported passenger/cabin/currency settings, and expired departure dates.
Airport inputs validate IATA shape; adapters use airport/timezone reference data
where supported. Future-date validation uses the server calendar date, not a
complete origin-local departure cutoff. Display currencies: IDR/USD/AUD/JPY.

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
in earlier sessions; evidence is archived in [P2–P4](docs/log/p2-p4.md). Current managed
sandbox restrictions can still prevent starting servers or browsers.

Web validation (from `apps/web`): `npm test` and `npm run build`. Browser
regressions: `npm run test:browser` after Chromium is installed with
`npx playwright install chromium`. This suite uses synthetic intercepted responses
and makes no provider calls. The latest archived P4.7 acceptance records 4 web
unit tests and 65 browser checks; see the
[P4.7 evidence](docs/log/research-cache-p4.6-p4.7.md).
Restricted sessions may require permission to start Chromium.

Offline P4.8 experiment checks:

```sh
.venv/bin/python -m pytest -c backend/pyproject.toml scripts/benchmarks/test_p48_instrumentation.py scripts/benchmarks/test_p48_failures.py scripts/benchmarks/test_p48_scheduler_review.py -q -rx
```

The P4.8 review/failure/instrumentation suite now passes all 22 tests; its former
cancellation/cooldown expected failure is a passing regression. Production scheduler
acceptance checks are in `backend/tests/integration/test_scheduler.py`. Controlled
performance comparisons use synthetic providers and disposable SQLite databases:

```sh
/usr/bin/caffeinate -i .venv/bin/python scripts/benchmarks/p49_scheduler_comparison.py --output /tmp/p49-new.jsonl --variant A0 --variant P49 --scenario candidate_replay_scaled --repeats 3
```

On non-macOS systems omit `caffeinate`. Live benchmark scripts require explicit
opt-in and are not part of default CI.

Full Xcode is still required for P5; command-line tools alone cannot build SwiftUI.
See [the phase checkpoints](docs/06_IMPLEMENTATION_CHECKPOINTS.md) for remaining work.

## P4.5 web refinement

The owner accepted the integrated web design, which is merged into main.
[P4.5 archive](docs/log/p4.5.md) records the design decisions, component map and
validation; [WORK_LOG.md](WORK_LOG.md) holds the current next task.
Integrated synthetic screenshots remain in
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
The web's source chooser starts all enabled, permitted sources selected and sends
explicit provider IDs; the backend validates the selection. The web shows
cache/shared provenance and provides **Run fresh search**, which creates a new
job with the same selections and `cache_mode=refresh`.

OctoTrip is available for owner-approved personal use by adding `octotrip` to
`ENABLED_PROVIDERS`, for example `skiplagged,swoop,octotrip`. Install backend live
extras for the airport timezone reference. It provides an indicative shortlist
with source-supplied sellers and baggage statements; hidden-city/self-transfer,
fare products and mandatory costs remain unknown. Nearby-airport candidates are
excluded from explicit-airport searches. Endpoint times use the validated airport
reference; complete operating-carrier/segment identity is not inferred.
OctoTrip caching and exact repricing remain disabled. Its conservative 900-second
result lifecycle applies to its observations independently of other sources'
fresh fares and the job's execution budget. Existing legacy deadlines/cutoffs are
preserved by migration; expired prices cannot be recovered.
Software defaults remain fake-only; source/accuracy evidence and owner approvals
are summarized in [WORK_LOG.md](WORK_LOG.md), with detailed evidence in
[docs/log/](docs/log/README.md).
