# 04 — Data, Persistence, and REST API Contracts

**Contract-first rule:** define stable versioned canonical JSON in OpenAPI. Both React and native SwiftUI consume the same models and statuses. These examples are **normative design direction**, not claims of an already deployed API; worker may refine field names once, in documented ADR before backend + clients ship.

## Request schema

```json
{
  "trip_type": "one_way",
  "origins": ["MEL"],
  "destinations": ["CGK", "DPS", "SUB"],
  "departure_date_from": "2026-12-12",
  "departure_date_through": "2026-12-20",
  "passengers": {"adults": 1},
  "cabin": "economy",
  "include_basic_economy": true,
  "max_stops": null,
  "checked_bags_required": false,
  "display_currency": "IDR",
  "point_of_sale_country": "ID",
  "include_hidden_city": false
}
```

Rules: dates are **local at origin airport**, inclusive. IATA uppercase, unique, valid codes; skip origin==destination. Default origin/destination selector is explicit airports, not an unbounded country search. `include_hidden_city=false` is the safe default and must not silently become true. Single adult/economy implemented for MVP, reject other unsupported combinations clearly. `max_stops` is null/0/1/2. Query size cap is configurable server-side.

## Suggested API (v1)

| Endpoint | Expected behavior |
|---|---|
| `GET /api/v1/health` | Service health, no secrets/provider credentials |
| `GET /api/v1/capabilities` | Enabled providers/capabilities, supported currencies/limits, terms-disabled source info without secrets |
| `POST /api/v1/searches` | Validate, atomically create durable job; return `202 Accepted` + job id/status link |
| `GET /api/v1/searches/{job_id}` | Query/job status, coverage and errors. Job ID requires auth/access token when externally reachable |
| `GET /api/v1/searches/{job_id}/results?sort=best_checked&cursor=...` | Paginated, stable itinerary groups with distinct offers and price status |
| `POST /api/v1/searches/{job_id}/cancel` | Idempotent cancel request, terminal state eventually |
| `POST /api/v1/searches/{job_id}/retry-failed` | Optional P4 convenience; requeue specific retryable pairs, never silently resets successes |
| `GET /api/v1/openapi.json` | Generated API specification |

For first implementation use polling (e.g. 2–5 s while visible) with exponential increase for long jobs; source-state metadata must be persisted. SSE is optional after polling works. Do not promise periodic polling while iOS is suspended.

### Example create response (illustrative)

```json
{
  "job_id": "018f...-opaque-random-id",
  "status": "queued",
  "created_at": "2026-11-09T10:00:00Z",
  "total_route_date_combinations": 27,
  "enabled_detailed_providers": ["skiplagged", "swoop"],
  "job_status_url": "/api/v1/searches/018f...-opaque-random-id"
}
```

### Example status response (illustrative)

```json
{
  "job_id": "018f...-opaque-random-id",
  "status": "partial",
  "phase": "verifying",
  "total_route_date_combinations": 27,
  "covered_route_date_combinations": 27,
  "total_provider_work_items": 54,
  "succeeded_provider_work_items": 52,
  "succeeded_empty": 4,
  "failed_provider_work_items": 2,
  "skipped_unsupported": 0,
  "inventory_completeness": "unknown",
  "priced_candidate_count": 44,
  "exact_reprice_attempted": 10,
  "exact_reprice_succeeded": 8,
  "provider_status": [
    {"provider_id": "skiplagged", "succeeded": 27, "failed": 0, "disabled_reason": null},
    {"provider_id": "swoop", "succeeded": 25, "failed": 2, "disabled_reason": null}
  ],
  "warnings": ["Some provider/date combinations failed; cheapest-found result is provisional."],
  "updated_at": "2026-11-09T10:05:00Z"
}
```

**Do not derive `covered_route_date_combinations` by summing provider successes**: unique route-date keys only. Final `completed` only if all required work reached successful/explicitly supported completion and no unresolved failures; otherwise `partial`, `failed`, or `cancelled`. Distinguish job phase from terminal status (e.g. `status=running, phase=verifying`); adjust sample accordingly in implementation.

### Results payload — normalized shape

```json
{
  "job_id": "018f...-opaque-random-id",
  "sort": "best_checked",
  "as_of": "2026-11-09T10:05:00Z",
  "next_cursor": null,
  "itineraries": [{
    "itinerary_id": "itin_abcd",
    "identity_confidence": "exact_segments",
    "origin": "MEL",
    "destination": "DPS",
    "departure_local": "2026-12-16T09:40:00+11:00",
    "arrival_local": "2026-12-16T19:05:00+08:00",
    "duration_minutes": 745,
    "stops": 1,
    "segments": [{
      "marketing_carrier": "XY", "operating_carrier": "XY", "flight_number": "XY123",
      "origin": "MEL", "destination": "SIN",
      "depart_at": "2026-12-16T09:40:00+11:00",
      "arrive_at": "2026-12-16T15:50:00+08:00"
    }],
    "offers": [{
      "quote_id": "quote_123", "provider_id": "swoop", "seller": "Illustrative Seller",
      "fare_family": "basic", "cabin": "economy", "basic_economy": true,
      "amount_original": "2850000", "currency_original": "IDR",
      "comparable_amount": "2850000", "comparable_currency": "IDR",
      "comparison_status": "eligible_total_known",
      "fee_completeness": "known_total", "checked_bag": "not_included",
      "hidden_city": "no", "self_transfer": "unknown",
      "price_status": "repriced_exact", "is_estimate": false,
      "retrieved_at": "2026-11-09T10:03:00Z",
      "repriced_at": "2026-11-09T10:04:00Z",
      "link": "https://example.org/synthetic-offer",
      "link_scope": "exact_offer",
      "warnings": []
    }]
  }]
}
```

All `XY...`, seller, prices and URLs in this example are **synthetic fixtures**. Full real segment arrays must include every leg; the abbreviated example is not a valid match fingerprint.

## Canonical types and exact semantics

- `Money`: `amount_decimal: Decimal` and ISO 4217 code internally; serialize as **string** in JSON to prevent JS float mistakes. `comparable_amount` may be `null` when unknown.
- `Itinerary`: `itinerary_id`, ordered complete segments (marketing and operating carriers, flight numbers, actual airports, `depart_at`, `arrive_at` with offsets), duration, stop count, ticket/transfer context if known, fingerprint and `identity_confidence`.
- `Offer`: own provider and seller, provider quote id/opaque handle (server-only), cabin and brand, original money, comparable money/FX, fare/tax/fee/baggage completeness, hidden-city and self-transfer classifications, source/observed timestamps, source evidence, URI/link scope, price state and warnings.
- `CoverageEntry`: provider + one route-date + attempt/outcome/retries/result-cap/completeness/errors/timestamps.
- `FXSnapshot`: base, quote, rate as decimal string, rate provider, retrieved at. Never take FX rate from arbitrary one quote and apply to other prices without recording policy.
- `ProviderQuoteHandle`: opaque provider-only repricing selector, encrypted/server-side or short-lived storage, never shown to clients.
- `SearchJob`: immutable submitted query and state, owner/authorization metadata, progress snapshots, cancel state, warning summary.

### Important nullable fields

`hidden_city`, `self_transfer`, `is_estimate`, baggage details, seller, fare family, provider completeness, exact-link availability may be unknown/null. **Unknown is not false.** Avoid naïve boolean defaults; choose explicit three-valued enums `yes/no/unknown` where needed. Separate missing from `0` for price, baggage, stops and retries.

### Status enum proposals

```text
JobStatus: queued | running | completed | partial | failed | cancelled
JobPhase: validating | discovering | searching | aggregating | verifying | finalizing | done
WorkStatus: pending | running | retry_wait | succeeded_results | succeeded_empty |
            failed_terminal | skipped_unsupported | cancelled
PriceStatus: repriced_exact | recent_search | indicative | changed_or_unavailable
ComparisonStatus: eligible_total_known | extra_cost_unknown |
                  missing_required_baggage | ineligible | currency_unresolved
IdentityConfidence: exact_segments | insufficient_identity
LinkScope: exact_offer | itinerary | generic_search | unavailable
ThreeValued: yes | no | unknown
```

## Database schema (minimal SQLite)

Suggested migration tables, with FK indexes and unique constraints; worker defines actual SQLAlchemy models and migration tests:

- `search_jobs(id PK, query_json, owner_hash nullable, status, phase, cancel_requested, created_at, updated_at, completed_at)`
- `work_items(id PK, job_id FK, provider_id, origin, destination, departure_date_local, work_type, target_key, status, attempts, next_attempt_at, leased_until, last_error_code, last_error_detail_sanitized, started_at, finished_at, UNIQUE(job_id, provider_id, origin, destination, departure_date_local, work_type, target_key))`
- `itineraries(id PK, job_id FK, fingerprint nullable, identity_confidence, normalized_route fields, duration_minutes, stops, UNIQUE(job_id, fingerprint) only when identity is complete)`
- `segments(id PK, itinerary_id FK, ordinal, marketing_carrier, operating_carrier, flight_number, origin, destination, departs_at_tz, arrives_at_tz)`
- `fare_quotes(id PK, itinerary_id FK, provider_id, seller, fare_family, raw_currency, raw_amount_decimal_text, comparable_currency, comparable_amount_decimal_text nullable, price_status, risk_flags, luggage/fees fields, provider_quote_handle_server_side, observed_at, repriced_at, link, link_scope, fx_snapshot_id FK nullable)`
- `quote_revisions(id PK, quote_id FK, revision_time, amount, currency, seller/fare_identity, reason)`
- `fx_snapshots(id PK, base, quote, rate_decimal_text, source, observed_at)`
- `provider_evidence(id PK, job_id FK, provider_id, work_item_id FK, sanitized_pointer, retrieved_at, expires_at)`

SQLite recommended: WAL mode, FK enabled, busy timeout, safe migrations, one queue-owning worker; connection/pool behavior tested. Don't store passenger PII (not required). Define evidence TTL and scrub raw payloads for secrets/signed URLs where necessary.

## Authentication and transport

- Local-only MVP can bind `127.0.0.1`, but **never expose unauthenticated job enumeration, cancellation or sensitive upstream selectors on a public endpoint**. Public deployment requires HTTPS, auth/session bearer or per-job capability token; opaque IDs alone are not sufficient authorization.
- Provider keys belong only in backend environment/secret store, never generated OpenAPI, frontend build or iOS app.
- Restrict CORS to configured web origin; apply per-client search creation limits; prevent arbitrary upstream URL injection and SSRF in booking link generation.
- Validate generated links: `https://` and allowed scheme/host policy where practical; links to provider/seller are never assumed safe based solely on raw results.
- OpenAPI versions and compatibility tests prevent accidental breaking changes when iOS version lags web.

## Contract acceptance

1. Same fixture produces same parsed TS and Swift models.
2. No floats used in price sorting or JSON-to-money conversion.
3. Errors and coverage counters are stable and mathematically consistent.
4. A provider-only key or selector is absent from all public JSON.
5. Cross-frontend results represent same itinerary groups and seller alternatives.
6. Client rendering works with null/unknown metadata and missing external booking link.
