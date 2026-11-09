# FlightFinder — Worker Implementation Handoff

**Version:** 1.0 · **Prepared:** 2026-11-09 · **Status:** Approved product direction, pending provider feasibility gates

> **START HERE.** This is an **implementation assignment**, not the earlier architecture-review-only assignment. The approved design is in the active documents below. A copy of the complete 23-section V4 proposal is included under `reference/` for detailed historical context. The active documents supersede it where instructions differ.

## Mission

Build a small, trustworthy service that finds the **cheapest eligible one-way flight found among the searched sources** across an inclusive range of departure dates and one or more IATA airport pairs. Slow searches are fine; accuracy, transparent coverage, and low running cost are more important. No booking/checkout. Two frontends eventually: responsive web and **genuinely native iOS**.

**Example only:** MEL → CGK, DPS, SUB; 2026-12-12 through 2026-12-20; 1 adult, economy, IDR. These are test fixtures, **not live fare claims**.

## Approved non-negotiables

1. **Python backend:** Python 3.12+, FastAPI, Pydantic v2, `httpx`, SQLite, SQLAlchemy/Alembic, `asyncio` and bounded long-running job worker. **No Rust.**
2. **Web:** React + TypeScript + Vite. **iOS:** SwiftUI + `URLSession`, native UI; both consume the same versioned REST/OpenAPI contract. Do not embed provider clients or Python scrapers in mobile/web frontends.
3. **Modular provider adapters:** start with feasibility testing Skiplagged MCP and `swoop`; future APIs can be added without editing search orchestration, ranking, or frontend code. Provider availability and permission are unproven until validated.
4. **Exhaustive *combination* coverage:** schedule every eligible origin × destination × departure-date for the enabled detailed-search providers. Calendar prices **only prioritize**, never prune the matrix. Do not claim exhaustive airline inventory.
5. **Preserve itinerary and offers separately:** one itinerary can have many seller/provider/fare offers. Deduplicate cautiously; retain provenance and fare restrictions.
6. **Price accuracy:** store original quoted currency, seller, checked time, fare details and price status; reprice strongest candidates when possible. Never call a cached quote "verified". UI must distinguish `repriced`, `recent_search`, `indicative`, `changed`, and errors.
7. **Safe default:** exclude hidden-city fares and unclassifiable hidden-city risk from default cheapest *normal-ticket* ranking; flag self-transfers. Include basic economy if offered, with restrictions explicitly labeled. Never invent baggage/fees.
8. **Partial success is useful but honestly labeled:** provider failure ≠ no flights; a completed airport/date matrix ≠ complete fare inventory; user may leave UI while server continues a durable search.
9. **Low-maintenance, lawful operation:** respect rate limits and terms; no evading blocks. Never assume commercial/mixed-source rights without checking them.
10. **No booking integration, price alerts, historical-price product, LLM, microservices, Redis/Celery/PostgreSQL by default.** Add only with a measured need.

## Read in this order

| File | Purpose / main owner |
|---|---|
| `01_PRODUCT_REQUIREMENTS_UX.md` | User behavior, ranking semantics, screens, constraints |
| `02_SYSTEM_ARCHITECTURE.md` | Boundaries, concurrency, durable jobs, package organization |
| `03_PROVIDERS_AGGREGATION_PRICING.md` | Required P0 provider proof, integration, dedup, repricing, compliance |
| `04_DATA_AND_API_CONTRACTS.md` | Concrete canonical schema, database tables, REST DTOs, examples |
| `05_WEB_AND_NATIVE_IOS.md` | Responsive React UI, SwiftUI app, client states and API parity |
| `06_IMPLEMENTATION_CHECKPOINTS.md` | Ordered work, tickets, acceptance gates, artifacts and stop conditions |
| `07_TESTING_AND_OPERATIONS.md` | Test matrix, local setup, privacy/security, reliability, release |
| `08_AGENT_START_PROMPT.md` | Copy/paste bootstrap prompt for a local coding agent |
| `reference/V4_FULL_DESIGN_REFERENCE.md` | Complete earlier 23-section specification, retained verbatim |

## Rules for worker agents

- **Do not begin with UI.** First run the provider feasibility gate (P0) and implement a fake-provider vertical slice.
- **Before changing the stack or architecture**, record the blocker and evidence in `WORK_LOG.md`; keep approved requirements intact.
- **No optimistic assumptions:** a README claim is not proof that an endpoint works for the route/filters, has permission for use, or returns accurate fares.
- **Never silently drop errors, dates, providers or fare uncertainty.** Track all in a coverage ledger.
- **No real airline/provider calls in default CI.** Live canaries are opt-in, low-rate, non-destructive, and compliant.
- **One phase at a time.** Deliver runnable code, tests, minimal reproduction commands, and update `WORK_LOG.md` at each gate.
- Store all monetary values with `Decimal` or integer minor-unit representation; `float` is forbidden for monetary calculations.
- Do not hard-code source-specific fields into API, web/iOS clients, ranking, matching, or core domain.
- All example prices/fixtures must be visibly labeled synthetic; do not invent provider outcomes.

## Target high-level implementation

```text
React web (Vite) ─┐
                  ├── HTTPS /api/v1 (FastAPI) ── Search service ── SQLite job/offer store
SwiftUI iOS ──────┘                                  │
                                                     ├── Scheduler / coverage ledger
                                                     ├── Provider registry
                                                     │    ├── Skiplagged MCP adapter
                                                     │    ├── swoop adapter
                                                     │    └── future adapters
                                                     ├── Canonical normalizer & matching
                                                     └── Pricing/verification/ranking
```

## Final delivery expected

- Working local backend, web app, and eventually native iOS project (P5).
- Configurable provider registry with at least one **validated usable** source; a second source **only if validated and permitted**.
- End-to-end tests using fake providers and sanitized contract fixtures; manual live canary evidence separate.
- API OpenAPI contract, migrations, `.env.example`, setup commands, and reproducible UX screenshots.
- A completion report with what works, what remains unverified, measured coverage, how to run, test results, and known risks.

**Definition of success:** a valid request produces an honest ranked set of fares (or an honest empty/partial state), with the exact coverage and price evidence behind each displayed result, and the same results are consumable from web and native iOS.
