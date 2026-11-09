# 06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria

This is an executable work order. Do **not** skip P0 or build a pretty UI over nonfunctional upstream data. A small fake-provider vertical slice must always work. Start with a local CLI API proof; build the server, then web, then iOS. Keep changes reviewable and testable.

## Project board / dependency chain

```text
P0 Provider gate ──┬──→ P1 Canonical domain + fake providers ──→ P2 Jobs + API
                  │                                         │
                  └── real provider fixtures ──→ P3 Integration + price checks
                                                         │
                                                         ▼
                                              P4 React web + hardening
                                                         │
                                                         ▼
                                              P5 Native SwiftUI iOS
                                                         │
                                                         ▼
                                              P6 E2E acceptance + release
```

Each phase must have: PR/commit, files changed, tests executed, screenshots if UI, recorded decisions, measured evidence, known blockers and checkbox status in `WORK_LOG.md`.

## P0 — Provider feasibility GO/NO-GO (do first)

**Tasks**
- [ ] Read all worker docs and archived V4 for context; create repo and `WORK_LOG.md`.
- [ ] Research current, primary provider docs/terms and pin source versions.
- [ ] Write `scripts/provider_probe_skiplagged.py`: connect via current supported MCP Python SDK, list tools, inspect actual schema, make a minimal compliant date/route search where permitted, save redacted response fixture.
- [ ] Write `scripts/provider_probe_swoop.py`: run one-way search with explicit basic-economy policy and low-rate repricing where permitted, save redacted response fixture.
- [ ] For both, test fields needed: complete segments, prices/currency, source timestamp/estimate flags, hidden-city indication, airline/seller, baggage, fare product, link and ability to check selected itinerary.
- [ ] Manually compare at least a few quotes with the provider/airline booking/search page if offered. Document search date/time, route, seller and fare equivalence. Do not pretend checkout price is accessible if it is not.
- [ ] Test failure conditions conservatively (synthetic mocks for most failures; no intentional hammering for rate-limit testing).
- [ ] Document legal-use, quota and reuse/aggregation permission. **Do not enable disallowed provider.**
- [ ] Deliver `docs/PROVIDER_POC_REPORT.md` (evidence/observed vs claimed/GO decision/mitigation).

**Gate:** at least one provider exposes usable, acceptable-to-use detailed one-way search for target route/date. If not, stop real provider integration, keep fake-provider engine, and report viable fallback rather than inventing data. Second source is conditional on operational/legal feasibility.

## P1 — Domain models, expansion, matching, normalization (offline)

**Tasks**
- [ ] Initialize Python package, formatter/linter/type checker, pytest and CI.
- [ ] Implement query validator: code normalization, dates inclusive, max combos, timezone/source currency policy, one-way/adult/economy restriction.
- [ ] Implement `expand_routes_and_dates()` pure function with 1×3×9 → 27 fixture.
- [ ] Define typed `Money`, `FlightSegment`, `ItineraryIdentity`, `FareQuote`, `SourceEvidence`, `CoverageEntry`, `PriceStatus`, `ProviderCapabilities`, `ProviderError`.
- [ ] Implement fake deterministic calendar and detailed providers with synthetic prices and configurable errors/delays.
- [ ] Implement conservative fingerprint and matching, preserving multiple offers and unmatched itineraries.
- [ ] Implement comparable cost and default safe ranking, excluding unsafe and unknown-required-cost candidates, while preserving raw advertised view.
- [ ] Unit test all conversions, identity, comparison and error classifications with no network.

**Gate:** offline CLI prints correct ranked synthetic results, seller offers, coverage plan and warnings. A future third provider can be added by an adapter and registry config only.

## P2 — SQLite persistence, durable scheduler, API contract

**Tasks**
- [ ] Implement SQLAlchemy models/Alembic initial migrations, FK/unique constraints, SQLite WAL and busy timeout; migration up/down tested against temporary DB.
- [ ] Implement job creation, immutable query snapshot, work item enumeration with uniqueness, atomic claim/lease, attempts, terminal/retry states and explicit disabled-provider entries.
- [ ] Implement worker loop with global per-provider semaphores/rate budgets, timeout, bounded retries respecting `Retry-After`, startup stale lease recovery and global job budget.
- [ ] Implement cancellation that prevents new work and preserves completed results. Document non-force-killable blocking provider threads.
- [ ] Implement stable REST v1: health, capabilities, POST searches, GET job, GET results, cancel; OpenAPI schema committed/generated.
- [ ] Add fake provider integration test exercising API → scheduler → SQLite → results with partial errors and restart recovery.
- [ ] Add abuse controls for job creation and proper authorization boundary for any non-localhost deployment.

**Gate:** start API and worker; POST fake query; poll accurately; restart worker mid-search; completed pairs persist; state resumes without duplicate fares; cancellation works. OpenAPI roundtrip contract tests pass.

## P3 — Real provider adapters, aggregation and repricing

**Tasks**
- [ ] Implement Skiplagged adapter from inspected P0 MCP schemas; safely handle missing/indicative data. Only enable if allowed.
- [ ] Implement swoop adapter using bounded synchronous thread worker if required; capture `is_complete`, source metadata, selectors, and `is_estimate`. Only enable if allowed.
- [ ] Set per-provider queue budgets and feature capability flags; source errors remain isolated.
- [ ] Implement optional calendar queue optimization that changes ordering but never prunes required detailed combinations.
- [ ] Persist normalized quotes + opaque reprice handle, dedup duplicate source responses, match identical full itineraries but retain different seller/fare quotes.
- [ ] Implement candidate shortlist for repricing (top ~10 plus 10% competitors, configurable), verify exact itinerary/fare consistency, re-rank on price changes, follow additional candidates when selected offers disappear.
- [ ] Implement currency conversion snapshot/policy and baggage/fee comparability with unknown states.
- [ ] Ensure hidden-city marked true/unknown cannot enter default best checked normal-ticket results.
- [ ] Include provider legal-use flags and optional source disablement; never enable Travelpayouts Search API in competing metasearch aggregator without permission.

**Gate:** actual low-volume compliant provider canary plus complete fake contract tests; best checked results carry accurate provider evidence; second provider if feasible; `partial` and incomplete coverage visible. No false “bookable” claim.

## P4 — React web + reliability hardening

**Tasks**
- [ ] Build typed React/Vite web client from OpenAPI; one-way multi-airport and date-range form with filters.
- [ ] Render current stage and provider coverage, live partial results, confidence and fare risk statuses.
- [ ] Results grouped by itinerary with seller offers, sort modes, unknown bag / self-transfer warnings, source timestamp and valid external link policy.
- [ ] Support refresh/recovery from authorized job id, cancellation and actionable errors.
- [ ] Add integration browser tests (Playwright optional if already in stack), responsive 375/768/1440 screenshots, a11y checks.
- [ ] Validate restart recovery, partial, no matches, all provider failures, currency mismatch, stale repricing and API quotas.
- [ ] Local deployment instructions, `.env.example`, no committed keys, structured logs and source health summary.

**Gate:** a user can start/completely monitor a fake or authorized live search in a browser, refresh mid-search, inspect source evidence and safely open provider link. Web UI makes no misleading accuracy claims.

## P5 — Native SwiftUI iOS

**Tasks**
- [ ] Create Xcode project, deployment target documented, `URLSession` client and typed `Codable` structs matching OpenAPI.
- [ ] Implement native airport chips/search, date inputs, filter settings, progress/status, itinerary cards/details, alternative sellers and external links.
- [ ] Resume prior job on foreground; handle offline/error states and long-running backend job without pretending iOS background execution is guaranteed.
- [ ] Support iPhone and iPad layouts, Dynamic Type, VoiceOver, dark mode, link handoff and safe credential storage.
- [ ] Add URLProtocol mock tests/model decoding tests and run manual simulator checks for all P4 state fixtures.

**Gate:** iOS displays same result order, prices, caveats and coverage as web for the same job id; UI is truly SwiftUI native, with no embedded scraper or checkout.

## P6 — Release and owner acceptance

**Tasks**
- [ ] Re-run automated suite, one clean-room installation, migrations, restart and cancellation recovery.
- [ ] Capture live low-volume provider canary results/date/permission/quote vs seller comparison; use no unsupported guarantees.
- [ ] Validate default hidden-city exclusion, unknown baggage, partial sources, duplicate offers and source link behavior.
- [ ] Deliver `README.md`, `.env.example`, `docs/PROVIDER_POC_REPORT.md`, `contracts/openapi.yaml`, test report, screenshots, known-risk list and `WORK_LOG.md`.
- [ ] Produce `RELEASE_SUMMARY.md` with exact commands, what was validated, what was not validated, remaining work and GO/CONDITIONAL GO/NO-GO per provider.

**Gate:** user can run end-to-end from documented steps with fake provider even without external credentials, and with validated real provider(s) where permitted.

## Agent collaboration / handoffs

A lead worker may split work into these independently reviewable streams **after P0**:

- **Backend/domain worker:** query expansion, Money, matching, ranker, tests; must not import external SDKs into domain.
- **Provider worker:** SDK probe, adapters, fixtures, permission report; must not change canonical schema without an ADR.
- **Backend/API worker:** durable jobs, OpenAPI, persistence, restart; must follow domain types.
- **Frontend worker:** React UI after v1 contract stabilizes; native iOS only after web/API parity.

Do not concurrently edit the same contract/schema files without coordination. QA remains a responsibility of each implementation worker; no separate QA agent required.

## Required task report at every checkpoint

```text
Phase:
Files changed:
Commands run / test results:
Functional demo:
Provider evidence / policy decision (if relevant):
Unresolved failures / assumptions:
Deviation from handoff (with justification):
Next smallest task:
```

## Explicit stop / escalation rules

Stop and request owner decision **only** for a fundamental incompatibility: both providers unusable/unpermitted; infrastructure or recurring cost materially above free/low-cost goal; unavoidable loss of safe hidden-city classification with no alternative; or a proposed feature changes non-negotiable scope. For ordinary tradeoffs, choose simplest safe option, document the decision and continue. Never replace genuine search with hardcoded public flight-price fixtures outside fake-provider test mode.
