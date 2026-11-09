# CheapWings

Personal-use, flexible-date, one-way flight comparison. Python 3.12+ backend;
React web and native SwiftUI iOS are later phases. P2 provides durable SQLite
jobs, a separate worker, and REST v1 using **synthetic fake fares only**.
Provider approvals and P0 evidence are in [WORK_LOG.md](WORK_LOG.md) and
[the provider report](docs/PROVIDER_POC_REPORT.md). Real adapters are P3.

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
- P2 adapters are async. P3 must isolate synchronous providers in a bounded
  executor: cancelling an await cannot force-kill a blocking thread. An adapter
  needs its own network timeout; do not release its actual execution slot early.
- Registry changes produce explicit skipped entries for removed/disabled
  adapters. Real provider flags cannot be enabled in P2 by environment typo.

## Access and budgets

Without `CHEAPWINGS_OWNER_TOKEN`, only direct loopback clients and localhost
Host headers are accepted. For LAN, proxy, or private-tunnel use, set a random
owner token of at least 32 characters **in both shells**, use HTTPS at the
boundary, and send `Authorization: Bearer <token>` on capabilities/search/job/
results/cancel requests. All jobs belong to this one owner; there is no multi-user
service or public deployment in P2. Do not log or commit the token. Set
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

Only normalized synthetic data is stored in P2; no raw provider payloads or PII.
Fake jobs persist until the owner removes the local DB with both services stopped.
Real-source cache/evidence TTL and selector retention must be implemented in P3
before storing live responses under the accepted personal-use terms.
Back up SQLite with its backup API or with both services stopped; copying only
the main file while WAL writes are active is unsafe. No network/paid services
are required for P2.

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
external provider. This managed session forbids localhost socket binding, so
process smoke must run in an unrestricted terminal; in-process acceptance passes.

Full Xcode is still required for P5; command-line tools alone cannot build SwiftUI.
See [the phase checkpoints](docs/06_IMPLEMENTATION_CHECKPOINTS.md) for remaining work.
