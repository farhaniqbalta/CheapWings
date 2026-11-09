# 07 — Test Matrix, Deployment, Observability, and Runbook

## Testing strategy

Tests are predominantly deterministic and offline: pure domain/engine unit tests, fake adapter integration tests and API contract tests. Real provider calls must be explicit opt-in canaries with tight provider-compliant budgets; they cannot run in normal CI.

### P0–P3 test matrix

| ID | Scenario | Expected behavior |
|---|---|---|
| T01 | MEL × (CGK,DPS,SUB) × 9 inclusive dates | 27 valid unique combinations |
| T02 | Reversed dates, invalid IATA, same origin-dest | Validation error/skip with reason; no silent search |
| T03 | Duplicate origin and destination codes | Deduplicate input, no double-priced work |
| T04 | Successful response with zero matches | `succeeded_empty`, not failed |
| T05 | Timeout, auth issue, malformed response | Failed provider work; not empty-success |
| T06 | 429 and `Retry-After` | Bounded backoff, no rapid loops or evasion |
| T07 | One provider fails, other succeeds | Partial usable results + provider failure ledger |
| T08 | All providers fail | `failed`, no false “no flights” |
| T09 | Same full itinerary across two sources | One itinerary, two distinct seller/product quotes |
| T10 | Different connection flight numbers | Separate itineraries |
| T11 | Incomplete segment/timezone identity | No forced dedup; `insufficient_identity` |
| T12 | Duplicate quote response after retry | Idempotent, not double counted |
| T13 | `USD`, `JPY`, `IDR` conversions | Decimal exactness, original values and FX snapshot preserved |
| T14 | Taxes/fees unknown | Not ranked as definite cheaper payable total |
| T15 | Checked bag required, allowance unknown | Separate price-incomplete tier |
| T16 | Basic economy cheapest | Included if policy on, with restrictions; never treated as hidden city |
| T17 | Hidden-city `yes` and `unknown` | Excluded from safe normal-ticket ranking |
| T18 | Self-transfer `yes`/`unknown` | Clearly labeled risk; no implied protected connection |
| T19 | Reprice fare increases/decreases | New price ranked; quote revision retained |
| T20 | Reprice selector gone or fare brand changed | Cannot inherit exact repriced label |
| T21 | Calendar cheapest is stale | Every requested detailed combo still searched |
| T22 | Provider truncates response | Combination covered, inventory completeness unknown/limited |
| T23 | Cancel while job runs | Stop new work, keep completed offers, final cancelled status |
| T24 | Kill worker mid-job and restart | Lease recovery; no duplicates/lost successes |
| T25 | Run concurrent jobs | Shared provider concurrency/rate budget respected |
| T26 | Missing provider link | UI explains link unavailable; no fabricated checkout URL |
| T27 | Malicious/untrusted provider text/link | Sanitized rendering; valid URL scheme/host checks; no script execution |
| T28 | Third fake provider added | No core ranking/API/frontend edits needed |
| T29 | Browser/iOS reconnect | Same job results and timestamps, no auto-created duplicate job |
| T30 | Provider cannot legally aggregate | Disabled with visible reason, no data illegally mixed |

Add provider-specific regression fixtures as live schemas evolve. Do not store actual users' booking or passenger details; MVP needs none.

### Contract / client tests

- Snapshots decode correctly in TypeScript and Swift `Codable`, including `null`, numeric decimal strings and unknown enum values (show safe fallback).
- Both clients display exactly the same best checked price, route and source status when fed same API fixture.
- Web keyboard navigation, focus, 375px responsive, invalid date form, no results, partial success, restart/cancel UI.
- iOS simulator (iPhone+iPad), voiceover/dynamic type, offline/foreground recovery, link open behavior.

### Property / invariant tests

- `0 ≤ unique_covered_combos ≤ total_combos`; per-provider work counts do not inflate unique combo coverage.
- Idempotent repeated provider response does not increase number of identical offers.
- Grouping identical complete segment sequences is order-independent; different segment sequences are not equal.
- Sorting normalized payable prices is deterministic at same FX snapshot and eligibility/status.
- A missing bag fee or source estimate cannot silently become a known total.
- Only exact matching fare repricing may set `price_status=repriced_exact`.
- Terminal work is not retried unless explicit operator action creates an auditable attempt.

## Local install and dev runbook — worker must implement and verify

The following are **target commands to make work**, not claims they are already functional:

```bash
# From repository root
python3 -m venv .venv
source .venv/bin/activate
pip install -e './backend[dev]'
cp .env.example .env
# edit config locally: database, enabled providers, per-provider budgets
alembic -c backend/alembic.ini upgrade head
uvicorn cheapwings.main:app --app-dir backend/src --reload

# In another terminal (single queue owner)
python -m cheapwings.worker

# Web frontend
cd apps/web
npm ci
npm run dev

# Test suite (offline, should require no keys)
pytest backend/tests -q
```

Reconcile package layout and Alembic import paths to ensure these commands actually work. Final README must have exact verified commands, Python/Node/Xcode requirements, seed/test data and troubleshooting for macOS developer environment.

## Configuration `.env.example`

Include at minimum (exact names can be chosen and documented):

```dotenv
APP_ENV=local
DATABASE_URL=sqlite:///./data/cheapwings.db
API_BIND_HOST=127.0.0.1
API_BIND_PORT=8000
CORS_ALLOWED_ORIGINS=http://localhost:5173
ENABLED_PROVIDERS=fake
MAX_ROUTE_DATE_COMBINATIONS=120
GLOBAL_MAX_ACTIVE_SEARCH_JOBS=2
PER_PROVIDER_MAX_CONCURRENCY=1
JOB_REPRICE_BUDGET=20
LIVE_CANARY_ENABLED=false
# Secrets only as needed, never checked into source control.
```

Use `fake` provider by default in development and tests. Enabled real sources require explicit permission and configuration. Never log API keys or full opaque seller tokens. Do not put `.env` in git.

## Operational safety

- **Deployment:** local-first, API behind HTTPS/private tunnel if accessed by mobile; SQLite backed up; one scheduler owner. Local-only API bound to loopback cannot be reached by physical iPhone until configured on LAN or secure hosted endpoint.
- **iOS physical device:** configure actual reachable HTTPS endpoint; respect Apple ATS requirements, avoid shipping insecure ATS exemptions just for convenience.
- **Restart recovery:** worker scans expired leases at startup, reclaims only eligible items, preserves completed offers and idempotent keys. Test crash during DB commit.
- **Data retention:** define job, quote, FX and provider raw evidence TTL; redact signed URLs, selectors and credentials from logs and fixtures; avoid violating source caching terms.
- **Rate limits:** per-provider concurrency/cooldowns globally across search jobs. Respect throttling; never evade identity-based restrictions.
- **Security:** auth or owner capability token before public access; per-user creation budgets; CORS allowlist; input constraints; URL validation; no arbitrary provider URLs embedded into server-side fetch.
- **Observability:** structured logs include `job_id`, `work_item_id`, provider id, attempt, error type, response elapsed time, stage and price evidence status (not secrets). Metrics: coverage %, provider failure %, repricing success %, end-to-end wall time, quote-vs-seller comparison mismatch rate (on small canary sample), incomplete-baggage proportion.
- **Database:** SQLite WAL, FK/unique enforcement, migration coverage, proper transactions. Move to server database/worker queue only when multi-instance usage justifies it.

## Release checklist

- [ ] Clean checkout install works with fake provider and **no credentials**.
- [ ] Offline tests are green and require no live external access.
- [ ] All documented endpoints match OpenAPI + example responses.
- [ ] Provider canary has source version/date/terms/low-rate evidence and explicit GO or NO-GO.
- [ ] External deployment access protected, no secrets in web bundle/iOS app.
- [ ] Jobs survive worker restart, cancellation and client disconnect.
- [ ] Web and iOS show matching results/caveats for same job.
- [ ] Nothing advertises prices as guaranteed or globally cheapest.
- [ ] Final `RELEASE_SUMMARY.md` gives test counts, sample coverage and price caveats, known limitations, setup and next steps.
