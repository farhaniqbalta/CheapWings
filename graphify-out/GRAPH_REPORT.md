# Graph Report - CheapWings  (2026-11-18)

## Corpus Check
- 311 files · ~474,215 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 29 file(s) not represented in the graph (top: (none) 15, .jsonl 6, .css 3)

## Summary
- 3624 nodes · 9119 edges · 227 communities (136 shown, 91 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 1577 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bc4f5b22`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Repository
- Registration
- Money
- SingleDateRouteQuery
- Measured Production
- skiplagged.py
- test_p48_failures.py
- sqlalchemy
- Itinerary UI
- rust/src/lib.rs
- Fli Provider
- routes.py
- Web API Client
- StatusVisuals.tsx
- repository.py
- Implementation checklist and gates
- Architecture Docs
- catalog.py
- asyncio
- WORK_LOG.md — Current State (keep under ~80 lines)
- Provider and result-cache research (2026-11-10)
- Throughput Experiment
- SwoopProvider
- Web Types
- Search Form
- Itinerary
- Search Query Model
- now_ms
- Web Dev Deps
- tsconfig App
- P5.05 — Native iOS search engine feasibility analysis
- test_search_cache.py
- Browser Test Tooling
- tsconfig Node
- P4.10 Locations Log
- MCPClient
- Provider Feasibility Docs
- 06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria
- RouteDate
- test_p3.py
- P4.11 Fli Log
- contracts.py
- json
- provider_probe_swoop.py
- AirportSelection
- MatchEngine
- Product Requirements
- P46 Browser Tests
- test_carrier_airport_change.py
- SourceOffer
- cheapwings-ffi/src/lib.rs
- Package Scripts
- Location Licenses
- Lint Config
- Browser Fixtures
- routes.py
- FliPage
- Icon Sprite
- Vite Env Types
- tsconfig Root
- test_ranking.py
- Web Entry HTML
- Favicon
- React Logo
- Package Init 65
- Package Init 74
- CheapWings P4.8 — Throughput, Concurrency & Reliability Experiment
- Provider feasibility evidence
- p412_pool_benchmark.py
- json
- swoop.py
- P4.5 UI/UX handover, intake and fixes
- P4.9 — Scheduler architecture, implementation and verification
- 19. Python Tech Stack Decision, Long-Running Jobs, and Cross-Platform Integration
- P4.8 — Provider interval benchmark and scheduling plan (2026-11-10)
- FlightFinder — Architecture & Design Review Handoff
- 17. Mandatory Multi-Provider Aggregation Architecture (restored; mandatory)
- 12. MVP Milestones and Checkpoints
- MeasuredProduction
- fake.py
- 18. Web + Native iOS Product Design
- 1. Product Intent, Requirements, and Non-Goals
- 2. Proposed Search Experience / UX
- 3. Candidate Data Sources and Due-Diligence Notes
- 15. Mandatory Deliverables from the Reviewing Agent
- 5. Search Algorithm, Coverage, and Failure Handling
- 6. Fare Data Model & Comparability
- Sendable
- 11. Minimal Test Plan and Evaluation Matrix
- 20. Mandatory Cross-Platform and Multi-Provider Acceptance Tests
- 4. Architecture Proposal
- 7. Price Verification Policy
- 8. Filtering and Travel Risks
- AGENTS.md
- CLAUDE.md
- test_overlap_429_retry_after_and_independent_provider
- MatchEngine
- p3_live_canary.py
- P4.12 — Shared global resource pool
- build_location_catalog.py
- asyncio
- ItineraryInfo
- create_app
- WorkStatus
- Fli probe — P5.06 spikes S1 (iPhone) and S3 (Swift off-device)
- PackageDescription
- money.rs
- Decodable
- fli-wreq/build.sh
- fli-wreq
- cheapwings-money-rs
- cheapwings-money-rs
- LocationCatalog
- test_p48_failures.py
- FetchedPage
- ComboStatus
- ranking.rs
- gen_core_fixtures.py
- StoreError
- S5Section
- DispatchDeferred
- build-ios.sh
- rust/build.sh
- FoundOffer
- core-s5
- SearchModel
- cheapwings-core
- cheapwings-ffi
- cheapwings-py
- CheapWingsCore
- cheapwings-store/src/lib.rs
- repository.py
- pytest
- StopReason
- Outcome
- CoreError
- cheapwings-core
- store.rs
- 06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria
- skiplagged.rs
- App
- build_location_catalog.py
- LocalInstant
- reply
- MCPReply
- NetworkMonitor
- .lane
- .note
- PlanError
- test_swoop_rpc.py
- View
- OfferRow
- ProbeResult
- SkiplaggedSearchProvider
- p5.05.md
- 01 — Product Requirements, Rules, and UX Acceptance
- OfferDetailView
- P5.4 — Skiplagged on the iPad
- SearchQuery
- ContinuedSearch
- toolReply

## God Nodes (most connected - your core abstractions)
1. `Repository` - 112 edges
2. `ProviderFailure` - 95 edges
3. `Registration` - 94 edges
4. `FakeProvider` - 81 edges
5. `JobRunner` - 66 edges
6. `SearchSession` - 63 edges
7. `SearchQuery` - 50 edges
8. `SearchModel` - 46 edges
9. `SearchEvent` - 43 edges
10. `FoundOffer` - 42 edges

## Surprising Connections (you probably didn't know these)
- `Task 2: Picker speed and correctness (P5.5 deferred minors)` --references--> `ItineraryInfo`  [INFERRED]
  docs/log/p5.6-plan.md → apps/ios/CheapWingsKit/Sources/CheapWingsKit/ItineraryInfo.swift
- `Global Constraints` --references--> `PacedRunner`  [INFERRED]
  docs/log/p5.4-plan.md → apps/ios/CheapWingsKit/Sources/CheapWingsKit/PacedRunner.swift
- `Rulings made during implementation` --references--> `FoundOffer`  [INFERRED]
  docs/log/p5.2.md → apps/ios/CheapWingsKit/Sources/CheapWingsKit/SearchEngine.swift
- `Verification` --references--> `SearchSession`  [INFERRED]
  docs/log/p5.2.md → apps/ios/CheapWingsKit/Sources/CheapWingsKit/SearchSession.swift
- `3. Native engine design and module ownership` --references--> `Money`  [INFERRED]
  docs/log/p5.05.md → backend/src/cheapwings/domain/money.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Planned SwiftUI shares backend contract and durable recovery** — docs_05_web_and_native_ios_swiftui_plan, docs_06_implementation_checkpoints_p5, readme_ios_planned [EXTRACTED 1.00]
- **Exact identity, exact money and unknown-safe rankings** — docs_03_providers_aggregation_pricing_itinerary_offer_identity, docs_03_providers_aggregation_pricing_decimal_money_fx, docs_01_product_requirements_ux_safe_and_advertised_rankings, docs_04_data_and_api_contracts_three_valued_unknowns [INFERRED 0.85]
- **Canonical fare evidence remains conservative across adapters and clients** — docs_03_providers_aggregation_pricing_money, docs_04_data_and_api_contracts_three_valued, docs_log_p4_11_fare_limits, readme_safe_ranking [INFERRED 0.95]

## Communities (227 total, 91 thin omitted)

### Community 0 - "Repository"
Cohesion: 0.08
Nodes (36): DispatchFailure, JobRunner, Logged, test_blocking_adapter_pool_sized_to_g_uses_real_threads(), search(), test_cooled_provider_stops_starting_and_others_take_the_pool(), test_headroom_lets_late_higher_priority_work_start_immediately(), test_headroom_unused_without_an_available_higher_priority_source() (+28 more)

### Community 1 - "Registration"
Cohesion: 0.20
Nodes (5): DecodeError, .description, partialPayload, schemaChanged, Page

### Community 2 - "Money"
Cohesion: 0.06
Nodes (33): _core_call(), minor_unit_exponent(), Money, UnknownCurrencyError, _python_api_result(), test_beyond_28_digits_is_exact(), test_beyond_96_bit_raises_instead_of_rounding(), test_core_module_is_rust() (+25 more)

### Community 3 - "SingleDateRouteQuery"
Cohesion: 0.07
Nodes (19): SearchProvider, SingleDateRouteQuery, OctotripProvider, HttpStartGate, offer_from_row(), VerificationRepository, test_octotrip_429_stops_unsent_peer_http(), test_octotrip_gate_covers_initialization_across_three_sessions() (+11 more)

### Community 4 - "Measured Production"
Cohesion: 0.19
Nodes (17): ReviewDispatcher, ReviewRepository, TimedFake, drain(), max_overlap(), query(), test_cooldown_occupies_no_execution_slot(), test_database_failure_surfaces_instead_of_silent_worker_loss() (+9 more)

### Community 5 - "skiplagged.py"
Cohesion: 0.11
Nodes (15): SearchEvent, comboFailed, item, offers, offersHidden, progress, providerStopped, started (+7 more)

### Community 6 - "test_p48_failures.py"
Cohesion: 0.06
Nodes (34): CODE_SIGN_STYLE, CURRENT_PROJECT_VERSION, GENERATE_INFOPLIST_FILE, INFOPLIST_KEY_UILaunchScreen_Generation, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPad, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPhone, MARKETING_VERSION, PRODUCT_BUNDLE_IDENTIFIER (+26 more)

### Community 7 - "sqlalchemy"
Cohesion: 0.12
Nodes (7): upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade()

### Community 8 - "Itinerary UI"
Cohesion: 0.13
Nodes (29): PriceStatus, PublicItinerary, PublicOffer, FareRiskNotice(), formatDuration(), ItineraryCard(), BAG_LABEL, COMPARISON_LABEL (+21 more)

### Community 9 - "rust/src/lib.rs"
Cohesion: 0.05
Nodes (43): as_minor_units(), cheapwings_core(), from_minor_units(), fx_convert(), minor_unit_exponent(), to_py(), as_minor_units(), best_checked_deal() (+35 more)

### Community 10 - "Fli Provider"
Cohesion: 0.19
Nodes (14): decoder(), payload(), provider(), query(), test_c3_real_threads_overlap_and_cancel_retains_physical_capacity(), fetch(), test_challenge_redirect_is_not_followed(), test_exact_prices_identity_and_conservative_evidence() (+6 more)

### Community 11 - "routes.py"
Cohesion: 0.05
Nodes (30): FliSearchProvider, FliTransport, PacedRunner, OfflineErrors, ProviderOutcome, failed, found, retry (+22 more)

### Community 12 - "Web API Client"
Cohesion: 0.12
Nodes (24): api, ApiError, BASE_URL, request(), TERMINAL_STATUSES, errorMessage(), getOwnerToken(), setOwnerToken() (+16 more)

### Community 13 - "StatusVisuals.tsx"
Cohesion: 0.18
Nodes (13): dependencies, react@^19.3.1, react-dom@^19.3.1, LABEL, P46SearchProgress(), PoolGauge(), ProviderBars(), SEGMENTS (+5 more)

### Community 14 - "repository.py"
Cohesion: 0.12
Nodes (16): Scheduler design requirements, Authentication and secret boundary, Canonical Money Itinerary Offer Coverage, Coverage and terminal statuses, 04 — Data, Persistence, and REST API Contracts, Normative versioned REST design, Normative versioned REST v1 and canonical DTOs, SQLite persistence schema direction (+8 more)

### Community 15 - "Implementation checklist and gates"
Cohesion: 0.12
Nodes (14): Baseline and checkpoint 1 — 2026-11-18, Execution decisions, P5.7 — Execution evidence, 1. Correct documentation and record the plan, 2. Connect existing Rust engine rules to Python, 3. Connect Fli and Skiplagged parsing, 4. Move remaining provider parsing into Rust, 5. Share scheduling policy; switch the web worker (+6 more)

### Community 16 - "Architecture Docs"
Cohesion: 0.08
Nodes (33): Synthetic browser regressions, CheapWings web, React TypeScript Vite thin client, Runtime private access, Memory-only web owner token, Intercepted Playwright browser regression suite, React Vite thin client, Bounded blocking provider execution (+25 more)

### Community 17 - "catalog.py"
Cohesion: 0.05
Nodes (37): ASSETCATALOG_COMPILER_APPICON_NAME, CODE_SIGN_STYLE, CURRENT_PROJECT_VERSION, GENERATE_INFOPLIST_FILE, INFOPLIST_KEY_CFBundleDisplayName, INFOPLIST_KEY_UILaunchScreen_Generation, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPad, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPhone (+29 more)

### Community 18 - "asyncio"
Cohesion: 0.11
Nodes (31): Settings, default_registry(), client_for(), request_data(), test_api_scheduler_results_contract(), test_auth_and_remote_boundary(), test_baggage_eligibility_and_snapshot_cursor(), test_capabilities_report_default_source_selection() (+23 more)

### Community 19 - "WORK_LOG.md — Current State (keep under ~80 lines)"
Cohesion: 0.07
Nodes (33): Authorized task boundaries, Preserve current baseline, 08 — Starting Prompt for a Local Coding Agent, Implementation invariants, Single reporting location, Canonical evidence-preserving extensions, Pre-restructure WORK_LOG header (baseline, full tracker, ledger, summary, deviations), 2026-11-09 empty-repo baseline (+25 more)

### Community 20 - "Provider and result-cache research (2026-11-10)"
Cohesion: 0.06
Nodes (32): request_snapshot(), Cache and OctoTrip implementation kickoff (2026-11-10), Current code audit — implications for caching, Dated provider evaluation — primary sources, not production approval, Final live acceptance and handover — cache + OctoTrip, Hosted endpoint preflight — actual observations and limits, Implementation checkpoint — durable cache and backend selection (in progress), Live owner search — cross-provider overlap confirmed (2026-11-10) (+24 more)

### Community 21 - "Throughput Experiment"
Cohesion: 0.12
Nodes (8): Experiment, post(), wrap(), observed(), test_octotrip_three_sessions_share_one_http_gate(), session(), test_response_timing_preserves_stream_bytes(), respond()

### Community 22 - "SwoopProvider"
Cohesion: 0.07
Nodes (17): rankLowestAdvertised(), SearchEngine, EmptyOutcome, formatChanged, noFlights, searchesFailed, ResumeInfo, SearchSession (+9 more)

### Community 23 - "Web Types"
Cohesion: 0.10
Nodes (18): AirportTransfer, ComparisonStatus, Coverage, Currency, IdentityConfidence, Job, JobPhase, JobStatus (+10 more)

### Community 24 - "Search Form"
Cohesion: 0.20
Nodes (16): ProviderCapability, SearchRequest, AirportMultiSelect(), Props, Props, SearchForm(), todayIso(), createLocationService() (+8 more)

### Community 25 - "Itinerary"
Cohesion: 0.09
Nodes (18): airport_transfers(), AirportTransfer, compute_fingerprint(), Itinerary, FlightSegment, build_itinerary(), RepriceRequest, segments() (+10 more)

### Community 26 - "Search Query Model"
Cohesion: 0.15
Nodes (6): GateTransport, Outcome, error, page, ParallelPacingTests, SleepGate

### Community 27 - "now_ms"
Cohesion: 0.06
Nodes (38): PRODUCT_BUNDLE_IDENTIFIER, platform, settings, sources, type, CODE_SIGNING_ALLOWED, GENERATE_INFOPLIST_FILE, INFOPLIST_KEY_UILaunchScreen_Generation (+30 more)

### Community 28 - "Web Dev Deps"
Cohesion: 0.13
Nodes (19): devDependencies, oxlint@^1.90.0, @types/node@^24.19.2, @types/react@^19.3.0, @types/react-dom@^19.3.0, typescript@~7.0.2, vite@^8.3.6, @vitejs/plugin-react@^6.1.2 (+11 more)

### Community 29 - "tsconfig App"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 30 - "P5.05 — Native iOS search engine feasibility analysis"
Cohesion: 0.11
Nodes (19): 10. Sources, facts and open questions, 1. Executive verdict, 2. Provider compatibility matrix, 3. Native engine design and module ownership, 5. Background / foreground behaviour (iOS), 6. Risk register (likelihood × impact, 1–5), 7. Experiment plan (proposal; nothing run; each needs owner approval), 8. Architecture decision record (+11 more)

### Community 31 - "test_search_cache.py"
Cohesion: 0.22
Nodes (21): ProviderResultCache, Counted, finish(), setup(), test_absolute_retention_deadline_expires_inherited_job_and_purges(), test_additive_migration_preserves_populated_work_attempt_and_quote_history(), test_cache_eviction_bytes_policy_revocation_and_filter_reapplication(), test_cache_reuse_is_independent_of_other_selected_sources() (+13 more)

### Community 32 - "Browser Test Tooling"
Cohesion: 0.13
Nodes (14): playwright@^1.65.0, dist, evidence, shots, dist, dist, job, pool (+6 more)

### Community 33 - "tsconfig Node"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 34 - "P4.10 Locations Log"
Cohesion: 0.16
Nodes (17): Exhaustive combination coverage, P4.10 historical offline acceptance, Backend authoritative Major resolution, Typed Major backend authority, Legacy IATA caller compatibility, P4.10 — Smart location selection, Catalog limitations, P4.10 staged localhost and authorized live wiring (+9 more)

### Community 36 - "Provider Feasibility Docs"
Cohesion: 0.13
Nodes (16): Exact decimal money and FX provenance, 03 — Provider Feasibility, Multi-Provider Aggregation, and Fare Accuracy, Normalized provider error taxonomy, Itinerary versus seller offer, Conservative itinerary identity and separate fare offers, Comparable exact money, Typed provider failures versus successful empty, P0 provider feasibility gate (+8 more)

### Community 37 - "06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria"
Cohesion: 0.10
Nodes (53): FakeProvider, Registration, FareQuote, now_ms(), Repository, test_pagination_freezes_incremental_quote_set(), payload(), test_airport_change_never_claims_ground_cost_is_known_on_reprice() (+45 more)

### Community 38 - "RouteDate"
Cohesion: 0.18
Nodes (10): combo_from_store(), plan_search(), PlanSearchError, Rejected, route_from_core(), route_to_core(), RouteDate, store::StoredRequest (+2 more)

### Community 39 - "test_p3.py"
Cohesion: 0.09
Nodes (33): ProviderFailure, SourceEvidence, ItinerarySummary, FXSnapshot, Offer, ProviderRepriceResult, ProviderSearchResult, aware_iso() (+25 more)

### Community 40 - "P4.11 Fli Log"
Cohesion: 0.11
Nodes (19): Historical usable quote verification, P4.11 — Fli as a fourth provider, Truthful failure and cache semantics, Fourth provider Fli public Google Flights page, P4.11 acceptance evidence, Explicit HTTP2 transport, Indicative Google quotes and generic search links, Historical HTTP2 live measurements (+11 more)

### Community 41 - "contracts.py"
Cohesion: 0.14
Nodes (20): capabilities(), worker_pool(), AirportTransfer, Capabilities, Coverage, Created, DTO, ExpiredObservation (+12 more)

### Community 42 - "json"
Cohesion: 0.04
Nodes (49): database(), require_current_schema(), main(), worker_lock(), test_worker_exclusive_ownership_and_schema(), blocking(), live_guard(), main() (+41 more)

### Community 43 - "provider_probe_swoop.py"
Cohesion: 0.13
Nodes (25): PublicOffer, public_offer(), shortlist(), ComparisonStatus, LinkScope, PriceStatus, ProviderErrorCode, ThreeValued (+17 more)

### Community 44 - "AirportSelection"
Cohesion: 0.20
Nodes (8): .body, AirportSelection, .majorIDs, AirportToken, airport, major, SelectionTests, What exists now

### Community 45 - "MatchEngine"
Cohesion: 0.45
Nodes (7): MatchEngine, _offer(), _seg(), test_different_connections_are_different_itineraries(), test_duplicate_quote_response_is_idempotent(), test_insufficient_identity_itineraries_never_merge(), test_same_itinerary_two_providers_groups_with_distinct_offers()

### Community 46 - "Product Requirements"
Cohesion: 0.15
Nodes (7): Measurements, ObservedProvider, observers(), make_send(), observed(), post(), utc()

### Community 47 - "P46 Browser Tests"
Cohesion: 0.28
Nodes (6): all, dist, job, offer(), richEntries, trip()

### Community 48 - "test_carrier_airport_change.py"
Cohesion: 0.09
Nodes (34): airport_changes(), CheckedOffers, cross_check(), currency_from_token(), decode_page(), extract_ds1(), filter_offers(), FliError (+26 more)

### Community 49 - "SourceOffer"
Cohesion: 0.18
Nodes (9): FxNote, skiplagged_parse(), skiplagged::SourceOffer, skiplagged_tool_payload(), SkiplaggedError, Failed, SkiplaggedPage, SourceOffer (+1 more)

### Community 50 - "cheapwings-ffi/src/lib.rs"
Cohesion: 0.15
Nodes (13): AirportChange, best_checked_deal(), fli_airport_changes(), fli_filter_offers(), fli_source_offer(), FliCheckedOffers, FliLeg, FliOffer (+5 more)

### Community 51 - "Package Scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:browser

### Community 52 - "Location Licenses"
Cohesion: 0.33
Nodes (5): Airportsdata and mwgg Airports MIT attribution, MIT airport data license, Airportsdata and mwgg Airports MIT attribution, MIT airport data license, P4.10 offline typed location catalog

### Community 53 - "Lint Config"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 54 - "Browser Fixtures"
Cohesion: 0.33
Nodes (3): capabilities, dist, job

### Community 55 - "routes.py"
Cohesion: 0.09
Nodes (7): fold(), LocationCatalog, MajorResolution, ResultsExpired, 4. Port-vs-drop matrix, Global Constraints, Task 1: Rust locations module, stops filter, airport changes

### Community 56 - "FliPage"
Cohesion: 0.29
Nodes (6): fli_cross_check(), fli_decode_page(), fli::FliPage, FliDecodeError, Failed, FliPage

### Community 57 - "Icon Sprite"
Cohesion: 0.67
Nodes (3): Bluesky, Discord, GitHub and X logos, Reusable SVG icon sprite, Purple documentation and social profile icons

### Community 60 - "test_ranking.py"
Cohesion: 0.11
Nodes (15): Catalog, CatalogError, Invalid, NoMajorMapping, StaleVersion, TooLong, TypeMismatch, UnknownLocation (+7 more)

### Community 75 - "CheapWings P4.8 — Throughput, Concurrency & Reliability Experiment"
Cohesion: 0.12
Nodes (16): Alternative architecture assessment, Authorization and method, CheapWings P4.8 — Throughput, Concurrency & Reliability Experiment, Experiment A — completed live results, Experiment B — offline Python scheduler stress, Experiment C — offline overlapping failure injection, Follow-up — requested C3/1s trials and swoop retry (2026-11-11 Jakarta), Follow-up sanitized per-search ledger (+8 more)

### Community 76 - "Provider feasibility evidence"
Cohesion: 0.12
Nodes (15): Claims vs observed, Claims vs observed, Combined P0 gate outcome, Fields present / absent (for canonical domain mapping), Follow-up probe items, Legal/compliance note (the real risk for swoop), Live sample (redacted selector/links kept short; full in fixture), Owner decisions (resolved 2026-11-09, per `docs/06` stop/escalation rule) (+7 more)

### Community 77 - "p412_pool_benchmark.py"
Cohesion: 0.11
Nodes (4): Broken, ResumeTests, Tfs, ThrowingStore

### Community 78 - "json"
Cohesion: 0.18
Nodes (6): FakeClock, .sleep, .sleeps, FakeTransport, page(), SearchEngineTests

### Community 79 - "swoop.py"
Cohesion: 0.08
Nodes (17): ProviderCapabilities, json_payload(), obj_dict(), exact_http_client(), observe(), ExactCapture, provider_failure(), retry_after() (+9 more)

### Community 80 - "P4.5 UI/UX handover, intake and fixes"
Cohesion: 0.13
Nodes (18): P2–P4 implementation log, Historical CGK to CTS cancelled review, P2 recorded acceptance, P3 adapter normalization and acceptance, P3 evidence-preserving provider adapters, P4 React implementation, P4 typed client and polling reliability, Polling effects and stale-page fencing (+10 more)

### Community 81 - "P4.9 — Scheduler architecture, implementation and verification"
Cohesion: 0.17
Nodes (12): Checkpoints 4–5 — implementation and offline verification, Confirmed runtime cause and correction — 2026-11-11, Latest local live search outcome — 2026-11-11, Local live-site wiring — 2026-11-11, Merge status correction — 2026-11-11, Owner merge handoff — 2026-11-11, Owner testing and publication authorization — 2026-11-11, P4.9 Checkpoints 1–3 — 2026-11-11, Option A approved (+4 more)

### Community 82 - "19. Python Tech Stack Decision, Long-Running Jobs, and Cross-Platform Integration"
Cohesion: 0.17
Nodes (12): 19.10 Native iOS design and lifecycle, 19.11 Deployment and operational risk, 19.12 Technology and provider review verdict, 19.1 Approved direction and rationale, 19.2 Why Python fits the workload, 19.3 Dependency selection and explicit constraints, 19.4 Typed provider contract and canonical behavior, 19.6 Search concurrency and provider pacing (+4 more)

### Community 83 - "P4.8 — Provider interval benchmark and scheduling plan (2026-11-10)"
Cohesion: 0.17
Nodes (12): Actual comparison, Current scheduler assessment and review findings, Expected performance using measured service times, P4.8 provider interval benchmark and scheduling plan, P4.8 — Provider interval benchmark and scheduling plan (2026-11-10), Per-request sanitized timing ledger, Phase 2 architecture — proposed only, Phase 3 implementation proposal — smallest changes and safety gates (+4 more)

### Community 84 - "FlightFinder — Architecture & Design Review Handoff"
Cohesion: 0.20
Nodes (10): 0. Instructions to the Reviewing Agent, 10. Provider Implementation Interface (Concept), 13. Key Risks, Challenges, and Mitigations, 14. Explicit Open Design Decisions for Reviewer, 16. Source Material (recheck before implementing), 21. Deliverables Required from Independent Reviewing Agent (V4 Addendum), 22. Copy-Paste Prompt to Launch Review (Current V4), 9. API / Events / Persistence Contract (Sketch) (+2 more)

### Community 85 - "17. Mandatory Multi-Provider Aggregation Architecture (restored; mandatory)"
Cohesion: 0.25
Nodes (8): 17.1 Pipeline, 17.2 Separate itinerary from offer, 17.3 Provider interface and capabilities, 17.4 Aggregation and ranking rules, 17.5 Isolation, compliance, and extensibility, 17.6 Additional independent reviewer deliverables, 17.7 Acceptance checkpoints, 17. Mandatory Multi-Provider Aggregation Architecture (restored; mandatory)

### Community 86 - "12. MVP Milestones and Checkpoints"
Cohesion: 0.29
Nodes (7): 12. MVP Milestones and Checkpoints, P0 — Provider Feasibility Gate (reviewer first), P1 — CLI / Engine Baseline, P2 — Provider Aggregation and Repricing, P3 — Web UI on versioned backend API, P4 — Reliability and Validation, P5 — Native iOS App (after backend/API is stable)

### Community 88 - "fake.py"
Cohesion: 0.09
Nodes (20): DateRibbon, .body, DayColumn, .background, .bar, .body, .date, .foreground (+12 more)

### Community 89 - "18. Web + Native iOS Product Design"
Cohesion: 0.33
Nodes (6): 18.1 Platform-level principles, 18.2 Search form fields and validation, 18.3 Mobile-first information architecture, 18.4 Example concrete UI behavior, 18.5 iOS specifically, 18. Web + Native iOS Product Design

### Community 90 - "1. Product Intent, Requirements, and Non-Goals"
Cohesion: 0.33
Nodes (6): 1.1 Problem, 1.2 Hard requirements (P0), 1.3 Design priorities, 1.4 Explicitly out of scope for MVP, 1.5 Questions the reviewer must decide, 1. Product Intent, Requirements, and Non-Goals

### Community 91 - "2. Proposed Search Experience / UX"
Cohesion: 0.33
Nodes (6): 2.1 Primary user journey, 2.2 Suggested page layout, 2.3 UI states and affordances, 2.4 Visual style, 2.5 Ranking controls, 2. Proposed Search Experience / UX

### Community 92 - "3. Candidate Data Sources and Due-Diligence Notes"
Cohesion: 0.33
Nodes (6): 3.1 Skiplagged MCP — proposed primary discovery/search adapter, 3.2 swoop (`saraswatayu/swoop`) — proposed detailed search / repricing adapter, 3.3 Optional source: omkarcloud/google-flights-scraper, 3.4 Fallback: paid hosted calendar / fare API, 3.5 Provider-selection criteria, 3. Candidate Data Sources and Due-Diligence Notes

### Community 93 - "15. Mandatory Deliverables from the Reviewing Agent"
Cohesion: 0.40
Nodes (5): 15. Mandatory Deliverables from the Reviewing Agent, A. `REVIEW_FINDINGS.md`, B. `PROVIDER_POC_REPORT.md`, C. `REVISED_IMPLEMENTATION_PLAN.md` (only if architecture should change), Required final answer to owner

### Community 94 - "5. Search Algorithm, Coverage, and Failure Handling"
Cohesion: 0.40
Nodes (5): 5.1 Expand combinations, 5.2 Calendar use, 5.3 Job lifecycle and provider errors, 5.4 Search strategy, 5. Search Algorithm, Coverage, and Failure Handling

### Community 95 - "6. Fare Data Model & Comparability"
Cohesion: 0.40
Nodes (5): 6.1 Canonical search query (illustrative), 6.2 Canonical quote/itinerary fields (minimum), 6.3 Trip identity vs quote identity, 6.4 Comparable-price policy, 6. Fare Data Model & Comparability

### Community 96 - "Sendable"
Cohesion: 0.48
Nodes (3): Decoded, Leg, Offer

### Community 97 - "11. Minimal Test Plan and Evaluation Matrix"
Cohesion: 0.50
Nodes (4): 11.1 Disposable PoC (before app implementation), 11.2 Test cases, 11.3 Quality bar / acceptance criteria, 11. Minimal Test Plan and Evaluation Matrix

### Community 98 - "20. Mandatory Cross-Platform and Multi-Provider Acceptance Tests"
Cohesion: 0.50
Nodes (4): 20.1 Provider aggregation tests, 20.2 Web/native iOS parity tests, 20.3 Price validation protocol, 20. Mandatory Cross-Platform and Multi-Provider Acceptance Tests

### Community 99 - "4. Architecture Proposal"
Cohesion: 0.50
Nodes (4): 4.1 Logical components (web + native iOS; remote search engine), 4.2 Recommended stack (approved direction, subject to provider feasibility review), 4.3 Proposed repository layout (illustrative), 4. Architecture Proposal

### Community 100 - "7. Price Verification Policy"
Cohesion: 0.50
Nodes (4): 7.1 Definitions, 7.2 Repricing steps, 7.3 Proposed practical success metric, 7. Price Verification Policy

### Community 101 - "8. Filtering and Travel Risks"
Cohesion: 0.50
Nodes (4): 8. Filtering and Travel Risks, Basic economy / low-cost carriers, Hidden-city / skiplagging, Self-transfer / separate tickets

### Community 105 - "test_overlap_429_retry_after_and_independent_provider"
Cohesion: 0.06
Nodes (36): airport_lookup_has_timezone(), catalog(), CATALOG, FingerprintCase, Fixtures, fixtures(), FIXTURES, fli_pages_match_python() (+28 more)

### Community 107 - "MatchEngine"
Cohesion: 0.23
Nodes (6): pytest_configure(), as_minor_units(), convert(), from_minor_units(), minor_unit_exponent(), _shadow()

### Community 108 - "p3_live_canary.py"
Cohesion: 0.14
Nodes (13): resolve_location(), plan_scope(), catalog(), selection(), test_ambiguous_cities_keep_distinct_ids_and_geography(), test_boundary_and_overlap_match_expansion(), test_catalog_rejects_inconsistent_data(), test_lookup() (+5 more)

### Community 109 - "P4.12 — Shared global resource pool"
Cohesion: 0.07
Nodes (20): BoundedCall, __init__(), test_bounded_swoop_executor_c3_has_actual_overlap_and_no_queue(), __init__(), __init__(), __init__(), 2. Implementation, 3. Configuration review (+12 more)

### Community 110 - "build_location_catalog.py"
Cohesion: 0.12
Nodes (8): .content, .detailLine, .flights, CarriersLine, .body, AirlineNames, Carrier, AirlineNamesTests

### Community 112 - "ItineraryInfo"
Cohesion: 0.15
Nodes (4): .spoken, ItineraryInfo, Layover, ItineraryInfoTests

### Community 113 - "create_app"
Cohesion: 0.15
Nodes (16): create_app(), cancel(), create_search(), get_job(), get_results(), health(), _exact_reprice_count(), instant() (+8 more)

### Community 114 - "WorkStatus"
Cohesion: 0.11
Nodes (18): main(), run_demo(), CoverageEntry, unique_covered_combinations(), WorkStatus, ScriptedOutcome, _entry(), test_failed_terminal_requires_error_code() (+10 more)

### Community 115 - "Fli probe — P5.06 spikes S1 (iPhone) and S3 (Swift off-device)"
Cohesion: 0.33
Nodes (5): Fli probe — P5.06 spikes S1 (iPhone) and S3 (Swift off-device), Offline check (no network), S1 — physical iPhone (needs full Xcode, owner-approved live requests), S3 — Swift off-device (macOS pre-check), What this does not do

### Community 117 - "money.rs"
Cohesion: 0.23
Nodes (13): as_minor_units(), EXPONENTS, from_minor_units(), fx_convert(), minor_unit_exponent(), MoneyError, InvalidDecimal, NotWholeMinorUnits (+5 more)

### Community 119 - "Decodable"
Cohesion: 0.06
Nodes (42): FingerprintCase, Fixtures, FixtureTests, InstantJ, LegJ, MoneyCase, OfferExpectJ, OfferJ (+34 more)

### Community 120 - "fli-wreq/build.sh"
Cohesion: 0.33
Nodes (5): DEVELOPER_DIR, IPHONEOS_DEPLOYMENT_TARGET, MACOSX_DEPLOYMENT_TARGET, PATH, build.sh script

### Community 128 - "LocationCatalog"
Cohesion: 0.16
Nodes (6): CatalogError, Failed, Location, LocationCatalog, MajorResolution, SearchPage

### Community 129 - "test_p48_failures.py"
Cohesion: 0.15
Nodes (16): lifespan(), fixture(), claim(), engine(), migrate(), query(), drain(), record() (+8 more)

### Community 130 - "FetchedPage"
Cohesion: 0.07
Nodes (21): FetchedPage, isAllowedFliRedirect(), RedirectPolicy, .refused, URLSessionFliTransport, PriceText, PriceTextTests, twoLegPage() (+13 more)

### Community 131 - "ComboStatus"
Cohesion: 0.50
Nodes (4): ComboStatus, Done, Failed, Pending

### Community 132 - "ranking.rs"
Cohesion: 0.38
Nodes (6): best_checked_deal(), lowest_advertised(), priced(), RankOffer, tier(), ranking_matches_python()

### Community 133 - "gen_core_fixtures.py"
Cohesion: 0.10
Nodes (24): test_generator_money_reference_runs_without_rust_core(), currency_token(), expected_offer(), fingerprint_cases(), fli_leg(), fli_page_cases(), fli_row(), fli_tfs_cases() (+16 more)

### Community 134 - "StoreError"
Cohesion: 0.18
Nodes (7): HiddenCount, ProviderStop, SearchStore, StoredCombo, StoredSearch, StoreError, Failed

### Community 137 - "build-ios.sh"
Cohesion: 0.33
Nodes (5): DEVELOPER_DIR, IPHONEOS_DEPLOYMENT_TARGET, MACOSX_DEPLOYMENT_TARGET, PATH, build-ios.sh script

### Community 138 - "rust/build.sh"
Cohesion: 0.33
Nodes (5): DEVELOPER_DIR, IPHONEOS_DEPLOYMENT_TARGET, MACOSX_DEPLOYMENT_TARGET, PATH, build.sh script

### Community 139 - "FoundOffer"
Cohesion: 0.07
Nodes (12): .offer, Date, .milliseconds, .stored, FoundOffer, .providerID, .shownPrice, SearchRequest (+4 more)

### Community 142 - "SearchModel"
Cohesion: 0.08
Nodes (8): .dayShift, SearchModel, .canResume, .canSearch, .plan, .planSummary, .searchTitle, .selectedSources

### Community 151 - "CheapWingsCore"
Cohesion: 0.07
Nodes (19): .body, Theme, BackgroundTasks, CheapWingsCore, CheapWingsKit, CryptoKit, FliProbe, FliWreq (+11 more)

### Community 152 - "cheapwings-store/src/lib.rs"
Cohesion: 0.09
Nodes (22): RouteDate, ComboStatus, Done, Failed, Pending, from_json(), json(), KEEP_SEARCHES (+14 more)

### Community 153 - "repository.py"
Cohesion: 0.09
Nodes (20): cache_key(), CacheRepository, without_handles(), write_session(), Base, FXRow, ItineraryRow, OperationAttempt (+12 more)

### Community 155 - "pytest"
Cohesion: 0.49
Nodes (8): _base(), test_include_hidden_city_defaults_false_and_does_not_silently_flip(), test_rejects_excessive_combination_count(), test_rejects_invalid_iata(), test_rejects_multi_adult_in_mvp(), test_rejects_reversed_dates(), test_rejects_roundtrip_in_mvp(), test_rejects_same_origin_and_destination()

### Community 156 - "StopReason"
Cohesion: 0.05
Nodes (32): .isGoogleStop, StoreTests, SearchPersistence, SearchStore, .isProviderStop, .storedText, StopReason, backgrounded (+24 more)

### Community 157 - "Outcome"
Cohesion: 0.14
Nodes (13): isAllowedRedirect(), Outcome, blockedRedirect, blockedSorry, blockedTraffic, crossCheckFailed, httpError, .mustStop (+5 more)

### Community 158 - "CoreError"
Cohesion: 0.29
Nodes (6): as_minor_units(), CoreError, Invalid, from_minor_units(), fx_convert(), minor_unit_exponent()

### Community 160 - "store.rs"
Cohesion: 0.16
Nodes (17): combos(), failed_combo_keeps_its_code(), finish_combo_is_idempotent(), fli_offer(), offer(), open(), pending_lists_unfinished_in_order(), provider_stops_round_trip() (+9 more)

### Community 162 - "06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria"
Cohesion: 0.12
Nodes (16): Provider feasibility and permission gate, 05 — Web + Native iOS Client Implementation, Polling and recovery design, Web first iOS second, Native SwiftUI implementation plan, Web and SwiftUI share remote search engine, 06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria, Fundamental incompatibility escalation (+8 more)

### Community 163 - "skiplagged.rs"
Cohesion: 0.13
Nodes (21): FliLeg, days_from_civil(), decimal_text(), fli_source_offer(), FxNote, naive_parts(), skiplagged_link(), skiplagged_parse() (+13 more)

### Community 164 - "App"
Cohesion: 0.14
Nodes (8): CheapWingsApp, .body, SizeApp, .body, SizeApp, .body, SizeApp, .body

### Community 168 - "LocalInstant"
Cohesion: 0.50
Nodes (4): fingerprint(), fp::LocalInstant, LocalInstant, Segment

### Community 173 - "reply"
Cohesion: 0.21
Nodes (5): FakeMCPTransport, MCPClientTests, reply(), SkiplaggedProviderTests, .combo

### Community 174 - "MCPReply"
Cohesion: 0.16
Nodes (10): TransportError, notHTTP, tooLarge, MCPError, badReply, http, MCPReply, MCPTransport (+2 more)

### Community 175 - "NetworkMonitor"
Cohesion: 0.15
Nodes (10): NetworkMonitor, Design direction (frontend-design pass, owner request 2026-11-14), Review Focus, Task 1: Offline pause and resume, Task 2: Picker speed and correctness (P5.5 deferred minors), Task 3: Visual design, VoiceOver, larger text, dark mode, narrow windows, Task 4: Phase close, What exists now (+2 more)

### Community 176 - ".lane"
Cohesion: 0.16
Nodes (5): LanePause, .remaining, RunEmitter, StopFlag, .isSet

### Community 179 - ".note"
Cohesion: 0.19
Nodes (9): .priceText, .body, CarrierPlate, .body, CompactPrice, FxText, SourcePlate, .body (+1 more)

### Community 180 - "PlanError"
Cohesion: 0.10
Nodes (21): fingerprint(), isoformat(), LocalInstant, Segment, civil_from_days(), days_from_civil(), format_date(), normalize() (+13 more)

### Community 191 - "test_swoop_rpc.py"
Cohesion: 0.21
Nodes (6): parse_search_response(), search(), test_adapter_rejects_short_error_before_normalization(), test_missing_or_malformed_payload_is_not_empty_success(), test_short_rpc_error_is_not_empty_success(), test_valid_empty_with_metadata_frame_is_preserved()

### Community 193 - "View"
Cohesion: 0.10
Nodes (21): AirportPicker, .body, AirportToggleRow, .body, ChipLabelStyle, PlaceAirports, PlaceLink, PlaceRow (+13 more)

### Community 195 - "OfferRow"
Cohesion: 0.17
Nodes (9): OfferRow, .codesLine, .hasLegs, .stopsText, ResultsView, .body, .session, SearchSession.Phase (+1 more)

### Community 197 - "ProbeResult"
Cohesion: 0.23
Nodes (5): FliProbe, ProbeResult, .summary, ProbeView, .body

### Community 198 - "SkiplaggedSearchProvider"
Cohesion: 0.22
Nodes (4): SkiplaggedFetch, outcome, page, SkiplaggedSearchProvider

### Community 199 - "p5.05.md"
Cohesion: 0.08
Nodes (19): Decision status, Owner decision (2026-11-13, after S5), P5.06 — Native engine spikes (S1–S5), Reproduce, Results, Global Constraints, Out of scope (later phases), P5.1 Shared Rust Core Implementation Plan (+11 more)

### Community 202 - "01 — Product Requirements, Rules, and UX Acceptance"
Cohesion: 0.10
Nodes (18): Accessible responsive UI, 01 — Product Requirements, Rules, and UX Acceptance, One-way adult economy flight finder, Flexible one-way finder scope, Query coverage differs from inventory completeness, Conservative fare ranking, Safe Best checked and Lowest advertised views, Honest results states (+10 more)

### Community 204 - "OfferDetailView"
Cohesion: 0.08
Nodes (22): .accessibilityText, Array, OfferDetailView, .body, .steps, .summary, Step, airport (+14 more)

### Community 206 - "P5.4 — Skiplagged on the iPad"
Cohesion: 0.12
Nodes (14): Final review (fresh subagent, Opus), Next, P5.4 — Skiplagged on the iPad, Global Constraints, Out of scope, P5.4 iPad Skiplagged Implementation Plan, Review Focus, Task 1: Rust core — Skiplagged parser, neutral offer, fixtures (+6 more)

### Community 208 - "SearchQuery"
Cohesion: 0.15
Nodes (7): SearchRequest, MaxStops, QueryValidationError, SearchQuery, MajorSelection, admit(), case()

### Community 213 - "toolReply"
Cohesion: 0.35
Nodes (3): RoutingMCPTransport, Sent, toolReply()

## Knowledge Gaps
- **249 isolated node(s):** `.majorCodes`, `.body`, `.foreground`, `Network`, `airport` (+244 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1253 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **91 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `What exists now` connect `FetchedPage` to `SearchQuery`, `create_app`, `SwoopProvider`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Are the 88 inferred relationships involving `Repository` (e.g. with `AirportTransfer` and `IdentityConfidence`) actually correct?**
  _`Repository` has 88 INFERRED edges - model-reasoned connections that need verification._
- **What connects `.majorCodes`, `.body`, `.foreground` to the rest of the system?**
  _249 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Repository` be split into smaller, more focused modules?**
  _Cohesion score 0.07692307692307693 - nodes in this community are weakly interconnected._
- **Why does `SearchEngine` connect `SwoopProvider` to `Sendable`, `FetchedPage`, `skiplagged.py`, `p5.05.md`, `routes.py`, `p412_pool_benchmark.py`, `SearchModel`, `json`, `Search Query Model`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Are the 40 inferred relationships involving `ProviderFailure` (e.g. with `JobRunner` and `ExactCapture`) actually correct?**
  _`ProviderFailure` has 40 INFERRED edges - model-reasoned connections that need verification._
- **Should `Money` be split into smaller, more focused modules?**
  _Cohesion score 0.06001984126984127 - nodes in this community are weakly interconnected._