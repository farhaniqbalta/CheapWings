# Graph Report - cheapwings-p6  (2026-11-20)

## Corpus Check
- 334 files · ~488,057 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 30 file(s) not represented in the graph (top: (none) 16, .jsonl 6, .css 3)

## Summary
- 3798 nodes · 9799 edges · 209 communities (164 shown, 45 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 1725 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bcaa6733`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- JobRunner
- Sendable
- test_core_fixtures.py
- ProviderFailure
- test_p49_review.py
- SearchEvent
- base
- Settings
- P46ResultsWorkspace.tsx
- rust/src/lib.rs
- test_fli.py
- ProviderPacing
- App.tsx
- repository.py
- 04 — Data, Persistence, and REST API Contracts
- P5.7 — Execution evidence
- P4.5 UI/UX handover, intake and fixes
- base
- DispatchDeferred
- WORK_LOG.md — Current State (keep under ~80 lines)
- Provider and result-cache research (2026-11-10)
- Experiment
- SearchSession
- types.ts
- SearchForm.tsx
- with
- GateTransport
- common
- package.json
- compilerOptions
- P5.05 — Native iOS search engine feasibility analysis
- test_search_cache.py
- p45-browser.mjs
- compilerOptions
- P4.10 — Smart location selection
- pytest
- .body
- Repository
- RouteDate
- BoundedCall
- P4.11 — Fli as a fourth provider
- base.py
- store.rs
- offer.py
- View
- p412_report.py
- cheapwings-store/src/lib.rs
- RouteHeader
- fli.rs
- SourceOffer
- cheapwings-ffi/src/lib.rs
- routes.py
- AirportSelection
- .oxlintrc.json
- domain/query.py
- contracts.py
- FliPage
- Reusable SVG icon sprite
- vite-env.d.ts
- tsconfig.json
- CatalogError
- index.html
- Web favicon: purple lightning bolt
- React atom logo SVG
- Web HTML entry
- SearchQuery
- cheapwings
- CheapWings P4.8 — Throughput, Concurrency & Reliability Experiment
- Provider feasibility evidence
- FoundOffer
- FakeClock
- test_api.py
- reply
- P4.9 — Scheduler architecture, implementation and verification
- 19. Python Tech Stack Decision, Long-Running Jobs, and Cross-Platform Integration
- P4.8 — Provider interval benchmark and scheduling plan (2026-11-10)
- FlightFinder — Architecture & Design Review Handoff
- 17. Mandatory Multi-Provider Aggregation Architecture (restored; mandatory)
- 12. MVP Milestones and Checkpoints
- test_p57_engine.py
- DaySummary
- 18. Web + Native iOS Product Design
- 1. Product Intent, Requirements, and Non-Goals
- 2. Proposed Search Experience / UX
- 3. Candidate Data Sources and Due-Diligence Notes
- 15. Mandatory Deliverables from the Reviewing Agent
- 5. Search Algorithm, Coverage, and Failure Handling
- 6. Fare Data Model & Comparability
- ContinuedSearch
- 11. Minimal Test Plan and Evaluation Matrix
- 20. Mandatory Cross-Platform and Multi-Provider Acceptance Tests
- 4. Architecture Proposal
- 7. Price Verification Policy
- 8. Filtering and Travel Risks
- AGENTS.md
- CLAUDE.md
- fixtures.rs
- cheapwings-py/src/lib.rs
- shadow_money.py
- 06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria
- ResumeTests
- OfferRow
- Tfs
- ItineraryInfo
- catalog
- datetime
- Fli probe — P5.06 spikes S1 (iPhone) and S3 (Swift off-device)
- WorkStatus
- money.rs
- references/query.py
- FixtureTests
- fli-wreq/build.sh
- fli-wreq
- .urlSession
- datetime
- cheapwings-money-rs
- cheapwings-money-rs
- ProbeView
- LocationCatalog
- test_overlap_429_retry_after_and_independent_provider
- MCPClient
- ComboStatus
- ranking.rs
- gen_core_fixtures.py
- StoreError
- expand_routes_and_dates
- CheapWings
- build-ios.sh
- rust/build.sh
- .start
- core-s5
- SearchModel
- SkiplaggedSearchProvider
- P5.06 — Native engine spikes (S1–S5)
- cheapwings-core/src/lib.rs
- cheapwings-core
- cheapwings-ffi
- cheapwings-py
- utc
- CheapWingsCore
- StoreError
- run_trial
- react
- test_swoop_rpc.py
- FakeProvider
- Outcome
- CoreError
- cheapwings-core
- Offer
- Review Focus
- CheapWings — Worker Implementation Handoff
- skiplagged.rs
- Foundation
- drain
- build_location_catalog.py
- LocalInstant
- Theme.swift
- p46-browser.mjs
- source-revision.sh
- SearchStore
- MCPReply
- update-expected-revision.sh
- .lane
- 05 — Web + Native iOS Client Implementation
- Money
- parity.py
- PlanError
- P6 — Release acceptance
- scripts
- ComboStatus
- subprocess
- toolReply
- Implementation checklist and gates
- browser.mjs
- Pre-restructure WORK_LOG header (baseline, full tracker, ledger, summary, deviations)
- XCTestCase
- PackageDescription
- SearchEngine
- Review Focus
- p45-browser.mjs
- open
- P5.4 — Skiplagged on the iPad
- provider_probe_swoop.py
- ProbeResult
- _core_call
- P5.5 — iPad feature parity
- skiplagged_cases
- dependencies
- NetworkMonitor
- OfferDetailView
- test_p57_engine.py
- money-pyo3/src/lib.rs
- fli-wreq/src/lib.rs
- StopReason
- deserialize

## God Nodes (most connected - your core abstractions)
1. `ProviderFailure` - 116 edges
2. `Repository` - 113 edges
3. `FakeProvider` - 94 edges
4. `Registration` - 94 edges
5. `JobRunner` - 66 edges
6. `SearchSession` - 63 edges
7. `Offer` - 47 edges
8. `SearchModel` - 46 edges
9. `SearchQuery` - 44 edges
10. `WORK_LOG.md — Current State (keep under ~80 lines)` - 44 edges

## Surprising Connections (you probably didn't know these)
- `Task 2: Picker speed and correctness (P5.5 deferred minors)` --references--> `ItineraryInfo`  [INFERRED]
  docs/log/p5.6-plan.md → apps/ios/CheapWingsKit/Sources/CheapWingsKit/ItineraryInfo.swift
- `5. Background / foreground behaviour (iOS)` --references--> `Instant`  [INFERRED]
  docs/log/p5.05.md → spikes/core-s5/swift-core/Sources/SwiftCore/SwiftCore.swift
- `3. Native engine design and module ownership` --references--> `Money`  [INFERRED]
  docs/log/p5.05.md → backend/src/cheapwings/domain/money.py
- `Rulings made during implementation` --references--> `SearchPersistence`  [INFERRED]
  docs/log/p5.3.md → apps/ios/CheapWingsKit/Sources/CheapWingsKit/Persistence.swift
- `Final review (fresh subagent, Opus)` --references--> `SearchSession`  [INFERRED]
  docs/log/p5.2.md → apps/ios/CheapWingsKit/Sources/CheapWingsKit/SearchSession.swift

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Planned SwiftUI shares backend contract and durable recovery** — docs_05_web_and_native_ios_swiftui_plan, docs_06_implementation_checkpoints_p5, readme_ios_planned [EXTRACTED 1.00]
- **Exact identity, exact money and unknown-safe rankings** — docs_03_providers_aggregation_pricing_itinerary_offer_identity, docs_03_providers_aggregation_pricing_decimal_money_fx, docs_01_product_requirements_ux_safe_and_advertised_rankings, docs_04_data_and_api_contracts_three_valued_unknowns [INFERRED 0.85]
- **Canonical fare evidence remains conservative across adapters and clients** — docs_03_providers_aggregation_pricing_money, docs_04_data_and_api_contracts_three_valued, docs_log_p4_11_fare_limits, readme_safe_ranking [INFERRED 0.95]

## Communities (209 total, 45 thin omitted)

### Community 0 - "JobRunner"
Cohesion: 0.09
Nodes (44): DispatchFailure, JobRunner, Registration, test_pagination_freezes_incremental_quote_set(), test_fli_real_normalization_api_prices_and_cache(), transport(), test_fli_uses_durable_shared_fetch_cancel_fencing_and_cache(), fetch() (+36 more)

### Community 1 - "Sendable"
Cohesion: 0.12
Nodes (9): Decoded, DecodeError, .description, partialPayload, schemaChanged, Leg, Offer, Page (+1 more)

### Community 2 - "test_core_fixtures.py"
Cohesion: 0.18
Nodes (9): UnknownCurrencyError, _python_api_result(), test_beyond_28_digits_is_exact(), test_core_module_is_rust(), test_missing_core_module_names_the_fix(), test_money_fixtures_through_python_api(), test_unknown_currency_raises_unknown_currency_error(), Task 4: Python backend uses Rust money (PyO3) (+1 more)

### Community 3 - "ProviderFailure"
Cohesion: 0.04
Nodes (46): ProviderFailure, SearchProvider, SingleDateRouteQuery, aware_iso(), json_payload(), exact_http_client(), observe(), ExactCapture (+38 more)

### Community 4 - "test_p49_review.py"
Cohesion: 0.20
Nodes (17): ReviewDispatcher, ReviewRepository, TimedFake, drain(), max_overlap(), query(), test_cooldown_occupies_no_execution_slot(), test_database_failure_surfaces_instead_of_silent_worker_loss() (+9 more)

### Community 5 - "SearchEvent"
Cohesion: 0.15
Nodes (14): SearchEvent, comboFailed, item, offers, offersHidden, progress, providerStopped, started (+6 more)

### Community 6 - "base"
Cohesion: 0.06
Nodes (34): CODE_SIGN_STYLE, CURRENT_PROJECT_VERSION, GENERATE_INFOPLIST_FILE, INFOPLIST_KEY_UILaunchScreen_Generation, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPad, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPhone, MARKETING_VERSION, PRODUCT_BUNDLE_IDENTIFIER (+26 more)

### Community 7 - "Settings"
Cohesion: 0.25
Nodes (12): lifespan(), Settings, default_registry(), require_current_schema(), main(), worker_lock(), test_fourth_registration_configuration_and_no_false_capabilities(), test_missing_optional_fli_is_disabled_with_install_reason() (+4 more)

### Community 8 - "P46ResultsWorkspace.tsx"
Cohesion: 0.13
Nodes (29): PriceStatus, PublicItinerary, PublicOffer, FareRiskNotice(), formatDuration(), ItineraryCard(), BAG_LABEL, COMPARISON_LABEL (+21 more)

### Community 9 - "rust/src/lib.rs"
Cohesion: 0.18
Nodes (22): as_minor_units(), best_checked_deal(), exponent(), EXPONENTS, fingerprint(), FingerprintCase, Fixtures, from_minor_units() (+14 more)

### Community 10 - "test_fli.py"
Cohesion: 0.21
Nodes (14): payload(), provider(), query(), test_c3_real_threads_overlap_and_cancel_retains_physical_capacity(), fetch(), test_challenge_redirect_is_not_followed(), test_exact_prices_identity_and_conservative_evidence(), test_fetch_pins_http2_and_preserves_json_price_lexemes() (+6 more)

### Community 11 - "ProviderPacing"
Cohesion: 0.07
Nodes (33): FliSearchProvider, FliTransport, PacedRunner, ProviderOutcome, failed, found, retry, stop (+25 more)

### Community 12 - "App.tsx"
Cohesion: 0.13
Nodes (23): api, ApiError, BASE_URL, request(), TERMINAL_STATUSES, errorMessage(), getOwnerToken(), setOwnerToken() (+15 more)

### Community 13 - "repository.py"
Cohesion: 0.09
Nodes (20): cache_key(), CacheRepository, without_handles(), Base, FareQuote, FXRow, ItineraryRow, OperationAttempt (+12 more)

### Community 14 - "04 — Data, Persistence, and REST API Contracts"
Cohesion: 0.09
Nodes (22): Scheduler design requirements, Same-offer exact repricing, Authentication and secret boundary, Canonical Money Itinerary Offer Coverage, Coverage and terminal statuses, 04 — Data, Persistence, and REST API Contracts, Normative versioned REST design, Normative versioned REST v1 and canonical DTOs (+14 more)

### Community 15 - "P5.7 — Execution evidence"
Cohesion: 0.14
Nodes (14): Baseline and checkpoint 1 — 2026-11-18, Checkpoint 2 — engine/PyO3, 2026-11-18, Checkpoint 3 — Fli and Skiplagged parsing, Decisions and review, Execution decisions, Offline verification, P5.7 — Execution evidence, PR #21 review update (+6 more)

### Community 16 - "P4.5 UI/UX handover, intake and fixes"
Cohesion: 0.09
Nodes (27): Synthetic browser regressions, CheapWings web, React TypeScript Vite thin client, Runtime private access, Memory-only web owner token, Intercepted Playwright browser regression suite, React Vite thin client, P2–P4 implementation log (+19 more)

### Community 17 - "base"
Cohesion: 0.05
Nodes (37): ASSETCATALOG_COMPILER_APPICON_NAME, CODE_SIGN_STYLE, CURRENT_PROJECT_VERSION, GENERATE_INFOPLIST_FILE, INFOPLIST_KEY_CFBundleDisplayName, INFOPLIST_KEY_UILaunchScreen_Generation, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPad, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPhone (+29 more)

### Community 19 - "WORK_LOG.md — Current State (keep under ~80 lines)"
Cohesion: 0.18
Nodes (7): Evidence and phase-history index, 2026-11-11 documentation cleanup, Approved deviations, WORK_LOG.md — Current State (keep under ~80 lines), Current next task, Owner-controlled publication, Personal-use provider decisions

### Community 20 - "Provider and result-cache research (2026-11-10)"
Cohesion: 0.06
Nodes (33): request_snapshot(), Cache and OctoTrip implementation kickoff (2026-11-10), Current code audit — implications for caching, Dated provider evaluation — primary sources, not production approval, Final live acceptance and handover — cache + OctoTrip, Hosted endpoint preflight — actual observations and limits, Implementation checkpoint — durable cache and backend selection (in progress), Live owner search — cross-provider overlap confirmed (2026-11-10) (+25 more)

### Community 21 - "Experiment"
Cohesion: 0.12
Nodes (7): Experiment, post(), wrap(), observed(), test_octotrip_three_sessions_share_one_http_gate(), test_response_timing_preserves_stream_bytes(), respond()

### Community 22 - "SearchSession"
Cohesion: 0.06
Nodes (20): EmptyOutcome, formatChanged, noFlights, searchesFailed, Phase, idle, running, stopped (+12 more)

### Community 23 - "types.ts"
Cohesion: 0.10
Nodes (17): AirportTransfer, ComparisonStatus, Coverage, ExpiredObservation, IdentityConfidence, Job, JobPhase, JobStatus (+9 more)

### Community 24 - "SearchForm.tsx"
Cohesion: 0.17
Nodes (17): Currency, ProviderCapability, SearchRequest, AirportMultiSelect(), Props, Props, SearchForm(), todayIso() (+9 more)

### Community 25 - "with"
Cohesion: 0.05
Nodes (44): name, runs-on, steps, timeout-minutes, concurrency, cancel-in-progress, group, run (+36 more)

### Community 26 - "GateTransport"
Cohesion: 0.14
Nodes (7): GateTransport, Outcome, error, page, ParallelPacingTests, SearchModelDates, SleepGate

### Community 27 - "common"
Cohesion: 0.06
Nodes (38): PRODUCT_BUNDLE_IDENTIFIER, platform, settings, sources, type, CODE_SIGNING_ALLOWED, GENERATE_INFOPLIST_FILE, INFOPLIST_KEY_UILaunchScreen_Generation (+30 more)

### Community 28 - "package.json"
Cohesion: 0.13
Nodes (19): devDependencies, oxlint@^1.90.0, @types/node@^24.19.2, @types/react@^19.3.0, @types/react-dom@^19.3.0, typescript@~7.0.2, vite@^8.3.6, @vitejs/plugin-react@^6.1.2 (+11 more)

### Community 29 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 30 - "P5.05 — Native iOS search engine feasibility analysis"
Cohesion: 0.15
Nodes (13): 10. Sources, facts and open questions, 1. Executive verdict, 2. Provider compatibility matrix, 3. Native engine design and module ownership, 5. Background / foreground behaviour (iOS), 6. Risk register (likelihood × impact, 1–5), 7. Experiment plan (proposal; nothing run; each needs owner approval), 8. Architecture decision record (+5 more)

### Community 31 - "test_search_cache.py"
Cohesion: 0.22
Nodes (21): ProviderResultCache, Counted, finish(), setup(), test_absolute_retention_deadline_expires_inherited_job_and_purges(), test_additive_migration_preserves_populated_work_attempt_and_quote_history(), test_cache_eviction_bytes_policy_revocation_and_filter_reapplication(), test_cache_reuse_is_independent_of_other_selected_sources() (+13 more)

### Community 32 - "p45-browser.mjs"
Cohesion: 0.17
Nodes (9): playwright@^1.65.0, dist, evidence, shots, dist, dist, job, pool (+1 more)

### Community 33 - "compilerOptions"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 34 - "P4.10 — Smart location selection"
Cohesion: 0.11
Nodes (22): Airportsdata and mwgg Airports MIT attribution, MIT airport data license, Airportsdata and mwgg Airports MIT attribution, MIT airport data license, Exhaustive combination coverage, P4.10 historical offline acceptance, Backend authoritative Major resolution, Typed Major backend authority (+14 more)

### Community 35 - "pytest"
Cohesion: 0.18
Nodes (11): QueryValidationError, SearchQuery, test_zero_routes_and_date_changes(), _base(), test_include_hidden_city_defaults_false_and_does_not_silently_flip(), test_rejects_excessive_combination_count(), test_rejects_invalid_iata(), test_rejects_multi_adult_in_mvp() (+3 more)

### Community 36 - ".body"
Cohesion: 0.15
Nodes (11): OfferRow, .codesLine, .dayShift, .hasLegs, .spoken, .stopsText, ResultsView, .body (+3 more)

### Community 37 - "Repository"
Cohesion: 0.12
Nodes (38): FakeProvider, write_session(), now_ms(), Repository, test_short_source_expiry_preserves_other_source_and_running_job(), test_actual_start_deadline_and_cooldown_survive_restart(), test_cancel_before_adapter_entry_makes_no_upstream_call(), test_continuous_new_jobs_do_not_starve_already_served_jobs() (+30 more)

### Community 38 - "RouteDate"
Cohesion: 0.22
Nodes (8): plan_search(), PlanSearchError, Rejected, route_to_core(), RouteDate, store::StoredRequest, StoredRequest, WorkItem

### Community 39 - "BoundedCall"
Cohesion: 0.07
Nodes (23): BoundedCall, __init__(), test_bounded_swoop_executor_c3_has_actual_overlap_and_no_queue(), __init__(), __init__(), __init__(), 1. Architecture review — P4.9 admission as merged, 2. Implementation (+15 more)

### Community 40 - "P4.11 — Fli as a fourth provider"
Cohesion: 0.11
Nodes (19): Historical usable quote verification, P4.11 — Fli as a fourth provider, Truthful failure and cache semantics, Fourth provider Fli public Google Flights page, P4.11 acceptance evidence, Explicit HTTP2 transport, Indicative Google quotes and generic search links, Historical HTTP2 live measurements (+11 more)

### Community 41 - "base.py"
Cohesion: 0.09
Nodes (29): main(), run_demo(), compute_fingerprint(), IdentityConfidence, Itinerary, build_itinerary(), ItineraryGroup, MatchEngine (+21 more)

### Community 42 - "store.rs"
Cohesion: 0.21
Nodes (16): combos(), failed_combo_keeps_its_code(), finish_combo_is_idempotent(), fli_offer(), offer(), pending_lists_unfinished_in_order(), provider_stops_round_trip(), prunes_to_newest_ten() (+8 more)

### Community 43 - "offer.py"
Cohesion: 0.12
Nodes (23): shortlist(), ComparisonStatus, LinkScope, PriceStatus, ProviderErrorCode, ThreeValued, offer_from_row(), VerificationRepository (+15 more)

### Community 44 - "View"
Cohesion: 0.13
Nodes (14): AirportPicker, .body, AirportToggleRow, .body, ChipLabelStyle, PlaceAirports, PlaceLink, PlaceRow (+6 more)

### Community 45 - "p412_report.py"
Cohesion: 0.29
Nodes (5): summarize(), cell(), fmt(), load(), main()

### Community 46 - "cheapwings-store/src/lib.rs"
Cohesion: 0.11
Nodes (10): from_json(), json(), KEEP_SEARCHES, MIGRATE_V2, SCHEMA_V1, SCHEMA_VERSION, sql(), StoredRequest (+2 more)

### Community 47 - "RouteHeader"
Cohesion: 0.12
Nodes (14): CheapWingsApp, .body, RouteHeader, .arrow, .body, SearchView, Side, destination (+6 more)

### Community 48 - "fli.rs"
Cohesion: 0.09
Nodes (41): airport_changes(), CheckedOffers, cross_check(), currency_from_token(), decode_page(), decode_row(), extract_ds1(), filter_offers() (+33 more)

### Community 49 - "SourceOffer"
Cohesion: 0.18
Nodes (9): FxNote, skiplagged_parse(), skiplagged::SourceOffer, skiplagged_tool_payload(), SkiplaggedError, Failed, SkiplaggedPage, SourceOffer (+1 more)

### Community 50 - "cheapwings-ffi/src/lib.rs"
Cohesion: 0.12
Nodes (16): AirportChange, best_checked_deal(), cheapwings_core_build_revision(), combo_from_store(), fli_airport_changes(), fli_filter_offers(), fli_source_offer(), FliCheckedOffers (+8 more)

### Community 51 - "routes.py"
Cohesion: 0.11
Nodes (5): MajorResolution, MajorSelection, CapacityExceeded, ResultsExpired, 4. Port-vs-drop matrix

### Community 52 - "AirportSelection"
Cohesion: 0.20
Nodes (9): .body, .body, AirportSelection, .majorIDs, AirportToken, airport, major, SelectionTests (+1 more)

### Community 53 - ".oxlintrc.json"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 55 - "contracts.py"
Cohesion: 0.10
Nodes (31): create_app(), cancel(), capabilities(), create_search(), get_job(), get_results(), health(), worker_pool() (+23 more)

### Community 56 - "FliPage"
Cohesion: 0.29
Nodes (6): fli_cross_check(), fli_decode_page(), fli::FliPage, FliDecodeError, Failed, FliPage

### Community 57 - "Reusable SVG icon sprite"
Cohesion: 0.67
Nodes (3): Bluesky, Discord, GitHub and X logos, Reusable SVG icon sprite, Purple documentation and social profile icons

### Community 60 - "CatalogError"
Cohesion: 0.08
Nodes (21): Catalog, CatalogError, AirportWithoutCode, DuplicateAirport, DuplicateLocation, Invalid, InvalidAssociation, InvalidMapping (+13 more)

### Community 75 - "CheapWings P4.8 — Throughput, Concurrency & Reliability Experiment"
Cohesion: 0.12
Nodes (16): Alternative architecture assessment, Authorization and method, CheapWings P4.8 — Throughput, Concurrency & Reliability Experiment, Experiment A — completed live results, Experiment B — offline Python scheduler stress, Experiment C — offline overlapping failure injection, Follow-up — requested C3/1s trials and swoop retry (2026-11-11 Jakarta), Follow-up sanitized per-search ledger (+8 more)

### Community 76 - "Provider feasibility evidence"
Cohesion: 0.13
Nodes (15): Claims vs observed, Claims vs observed, Combined P0 gate outcome, Fields present / absent (for canonical domain mapping), Follow-up probe items, Legal/compliance note (the real risk for swoop), Live sample (redacted selector/links kept short; full in fixture), Owner decisions (resolved 2026-11-09, per `docs/06` stop/escalation rule) (+7 more)

### Community 77 - "FoundOffer"
Cohesion: 0.08
Nodes (10): .offer, .stored, FoundOffer, .providerID, .shownPrice, rankLowestAdvertised(), SearchRequest, .country (+2 more)

### Community 78 - "FakeClock"
Cohesion: 0.18
Nodes (6): FakeClock, .sleep, .sleeps, FakeTransport, page(), SearchEngineTests

### Community 79 - "test_api.py"
Cohesion: 0.19
Nodes (19): client_for(), request_data(), test_auth_and_remote_boundary(), test_baggage_eligibility_and_snapshot_cursor(), test_capabilities_report_default_source_selection(), test_invalid_input_no_job(), test_openapi_committed_and_response_shapes(), test_quota_and_cancel() (+11 more)

### Community 80 - "reply"
Cohesion: 0.23
Nodes (5): FakeMCPTransport, MCPClientTests, reply(), SkiplaggedProviderTests, .combo

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
Cohesion: 0.18
Nodes (10): 0. Instructions to the Reviewing Agent, 10. Provider Implementation Interface (Concept), 13. Key Risks, Challenges, and Mitigations, 14. Explicit Open Design Decisions for Reviewer, 16. Source Material (recheck before implementing), 21. Deliverables Required from Independent Reviewing Agent (V4 Addendum), 22. Copy-Paste Prompt to Launch Review (Current V4), 9. API / Events / Persistence Contract (Sketch) (+2 more)

### Community 85 - "17. Mandatory Multi-Provider Aggregation Architecture (restored; mandatory)"
Cohesion: 0.25
Nodes (8): 17.1 Pipeline, 17.2 Separate itinerary from offer, 17.3 Provider interface and capabilities, 17.4 Aggregation and ranking rules, 17.5 Isolation, compliance, and extensibility, 17.6 Additional independent reviewer deliverables, 17.7 Acceptance checkpoints, 17. Mandatory Multi-Provider Aggregation Architecture (restored; mandatory)

### Community 86 - "12. MVP Milestones and Checkpoints"
Cohesion: 0.29
Nodes (7): 12. MVP Milestones and Checkpoints, P0 — Provider Feasibility Gate (reviewer first), P1 — CLI / Engine Baseline, P2 — Provider Aggregation and Repricing, P3 — Web UI on versioned backend API, P4 — Reliability and Validation, P5 — Native iOS App (after backend/API is stable)

### Community 87 - "test_p57_engine.py"
Cohesion: 0.13
Nodes (10): catalog(), plan_scope(), test_catalog_major_messages_and_order(), test_catalog_preserves_complete_records_and_order(), test_catalog_unicode_casefold_matches_reference(), test_fingerprint_matches_frozen_reference(), test_fixture_generators_do_not_call_rust_engine(), test_invalid_ranking_amount_raises() (+2 more)

### Community 88 - "DaySummary"
Cohesion: 0.11
Nodes (16): DateRibbon, .body, DayColumn, .background, .bar, .body, .date, .foreground (+8 more)

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

### Community 105 - "fixtures.rs"
Cohesion: 0.05
Nodes (37): airport_lookup_has_timezone(), catalog(), CATALOG, fingerprint_matches_python(), FingerprintCase, Fixtures, fixtures(), FIXTURES (+29 more)

### Community 106 - "cheapwings-py/src/lib.rs"
Cohesion: 0.10
Nodes (17): as_minor_units(), catalog_error(), cheapwings_core(), fingerprint(), fli_extract_ds1(), fli_parse(), from_minor_units(), fx_convert() (+9 more)

### Community 107 - "shadow_money.py"
Cohesion: 0.25
Nodes (6): pytest_configure(), as_minor_units(), convert(), from_minor_units(), minor_unit_exponent(), _shadow()

### Community 108 - "06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria"
Cohesion: 0.08
Nodes (29): Accessible responsive UI, 01 — Product Requirements, Rules, and UX Acceptance, One-way adult economy flight finder, Flexible one-way finder scope, Query coverage differs from inventory completeness, Conservative fare ranking, Safe Best checked and Lowest advertised views, Honest results states (+21 more)

### Community 109 - "ResumeTests"
Cohesion: 0.10
Nodes (5): SearchPersistence, Broken, ResumeTests, Tfs, ThrowingStore

### Community 110 - "OfferRow"
Cohesion: 0.17
Nodes (4): .flights, AirlineNames, Carrier, AirlineNamesTests

### Community 112 - "ItineraryInfo"
Cohesion: 0.12
Nodes (7): OfferDetailView, .steps, .summary, .detailLine, ItineraryInfo, Layover, ItineraryInfoTests

### Community 113 - "catalog"
Cohesion: 0.19
Nodes (11): resolve_location(), catalog(), LocationCatalog, selection(), test_ambiguous_cities_keep_distinct_ids_and_geography(), test_boundary_and_overlap_match_expansion(), test_catalog_rejects_inconsistent_data(), test_lookup() (+3 more)

### Community 114 - "datetime"
Cohesion: 0.09
Nodes (10): airport_transfers(), AirportTransfer, ProviderCapabilities, decimal_value(), money(), obj_dict(), airport_zone(), _airports() (+2 more)

### Community 115 - "Fli probe — P5.06 spikes S1 (iPhone) and S3 (Swift off-device)"
Cohesion: 0.33
Nodes (5): Fli probe — P5.06 spikes S1 (iPhone) and S3 (Swift off-device), Offline check (no network), S1 — physical iPhone (needs full Xcode, owner-approved live requests), S3 — Swift off-device (macOS pre-check), What this does not do

### Community 116 - "WorkStatus"
Cohesion: 0.24
Nodes (8): CoverageEntry, unique_covered_combinations(), WorkStatus, _entry(), test_failed_terminal_requires_error_code(), test_failure_is_not_counted_as_covered(), test_succeeded_empty_cannot_carry_error_code(), test_unique_covered_combinations_does_not_double_count_providers()

### Community 117 - "money.rs"
Cohesion: 0.23
Nodes (13): as_minor_units(), EXPONENTS, from_minor_units(), fx_convert(), minor_unit_exponent(), MoneyError, InvalidDecimal, NotWholeMinorUnits (+5 more)

### Community 118 - "references/query.py"
Cohesion: 0.24
Nodes (3): expand_routes_and_dates(), RouteDateCombo, MaxStops

### Community 119 - "FixtureTests"
Cohesion: 0.06
Nodes (38): FingerprintCase, Fixtures, FixtureTests, InstantJ, LegJ, MoneyCase, OfferExpectJ, OfferJ (+30 more)

### Community 120 - "fli-wreq/build.sh"
Cohesion: 0.33
Nodes (5): DEVELOPER_DIR, IPHONEOS_DEPLOYMENT_TARGET, MACOSX_DEPLOYMENT_TARGET, PATH, build.sh script

### Community 124 - "datetime"
Cohesion: 0.04
Nodes (33): upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), live_guard() (+25 more)

### Community 127 - "ProbeView"
Cohesion: 0.16
Nodes (6): WreqProbe, .body, ProbeView, .body, S5Section, .body

### Community 128 - "LocationCatalog"
Cohesion: 0.16
Nodes (6): CatalogError, Failed, Location, LocationCatalog, MajorResolution, SearchPage

### Community 129 - "test_overlap_429_retry_after_and_independent_provider"
Cohesion: 0.17
Nodes (17): fixture(), claim(), engine(), migrate(), query(), reg(), drain(), record() (+9 more)

### Community 131 - "ComboStatus"
Cohesion: 0.50
Nodes (4): ComboStatus, Done, Failed, Pending

### Community 132 - "ranking.rs"
Cohesion: 0.31
Nodes (8): best_checked_deal(), ExactAmount, lowest_advertised(), priced(), RankOffer, tier(), validate_amount(), ranking_matches_python()

### Community 133 - "gen_core_fixtures.py"
Cohesion: 0.15
Nodes (20): currency_token(), expected_offer(), fingerprint_cases(), fli_leg(), fli_page_cases(), fli_row(), fli_tfs_cases(), instant() (+12 more)

### Community 134 - "StoreError"
Cohesion: 0.18
Nodes (7): HiddenCount, ProviderStop, SearchStore, StoredCombo, StoredSearch, StoreError, Failed

### Community 135 - "expand_routes_and_dates"
Cohesion: 0.35
Nodes (7): expand_routes_and_dates(), RouteDateCombo, _query(), test_1x3x9_expands_to_27_combinations(), test_combos_are_unique_and_deterministic_order(), test_duplicate_input_codes_are_deduplicated_before_expansion(), test_same_origin_destination_pair_is_skipped()

### Community 136 - "CheapWings"
Cohesion: 0.10
Nodes (25): Bounded blocking provider execution, API application domain dependency boundaries, Dependency boundary, 02 — System Architecture and Runtime Boundaries, Durable job and work state, Capability-driven provider abstraction, Provider capability protocols, Fare evidence tiers (+17 more)

### Community 137 - "build-ios.sh"
Cohesion: 0.33
Nodes (5): DEVELOPER_DIR, IPHONEOS_DEPLOYMENT_TARGET, MACOSX_DEPLOYMENT_TARGET, PATH, build-ios.sh script

### Community 138 - "rust/build.sh"
Cohesion: 0.33
Nodes (5): DEVELOPER_DIR, IPHONEOS_DEPLOYMENT_TARGET, MACOSX_DEPLOYMENT_TARGET, PATH, build.sh script

### Community 142 - "SearchModel"
Cohesion: 0.07
Nodes (10): ContinuedSearch, SearchModel, .canResume, .canSearch, .plan, .planSummary, .searchTitle, .selectedSources (+2 more)

### Community 144 - "SkiplaggedSearchProvider"
Cohesion: 0.22
Nodes (4): SkiplaggedFetch, outcome, page, SkiplaggedSearchProvider

### Community 145 - "P5.06 — Native engine spikes (S1–S5)"
Cohesion: 0.29
Nodes (7): Decision status, Findings, Owner decision (2026-11-13, after S5), P5.06 — Native engine spikes (S1–S5), Reproduce, Results, S5 — Rust core vs Swift core on iPad (follow-up, same day)

### Community 150 - "utc"
Cohesion: 0.20
Nodes (6): Measurements, observers(), make_send(), observed(), post(), utc()

### Community 151 - "CheapWingsCore"
Cohesion: 0.09
Nodes (9): OfflineErrors, SearchProvider, BackgroundTasks, CheapWingsCore, CheapWingsKit, CryptoKit, Foundation, os (+1 more)

### Community 152 - "StoreError"
Cohesion: 0.20
Nodes (7): Store, StoredCombo, StoredOffer, StoredSearch, StoreError, NotFound, Open

### Community 153 - "run_trial"
Cohesion: 0.12
Nodes (6): database(), migrated(), MeasuredProduction, migrated(), run_trial(), admit()

### Community 154 - "react"
Cohesion: 0.27
Nodes (10): ProviderProgress, WorkerPool, LABEL, P46SearchProgress(), PoolGauge(), ProviderBars(), SEGMENTS, SOURCE_NAMES (+2 more)

### Community 155 - "test_swoop_rpc.py"
Cohesion: 0.16
Nodes (10): parse_search_response(), search(), test_guard_keeps_sdk_priced_offer_construction(), test_missing_or_malformed_payload_is_not_empty_success(), test_short_rpc_error_is_not_empty_success(), test_valid_empty_with_metadata_frame_is_preserved(), fingerprint_cases(), instant() (+2 more)

### Community 156 - "FakeProvider"
Cohesion: 0.22
Nodes (12): ScriptedOutcome, test_api_scheduler_results_contract(), test_provider_specific_timeout_extends_lease_without_changing_other_sources(), test_timeout_and_unexpected_error_are_not_empty(), _query(), test_fake_provider_labels_prices_as_synthetic(), test_fake_provider_respects_idr_zero_minor_units(), test_fake_provider_respects_include_basic_economy_false() (+4 more)

### Community 157 - "Outcome"
Cohesion: 0.17
Nodes (12): Outcome, blockedRedirect, blockedSorry, blockedTraffic, crossCheckFailed, httpError, .mustStop, networkError (+4 more)

### Community 158 - "CoreError"
Cohesion: 0.29
Nodes (6): as_minor_units(), CoreError, Invalid, from_minor_units(), fx_convert(), minor_unit_exponent()

### Community 160 - "Offer"
Cohesion: 0.08
Nodes (27): SourceEvidence, ItinerarySummary, FXSnapshot, Offer, FlightSegment, ProviderRepriceResult, ProviderSearchResult, RepriceRequest (+19 more)

### Community 161 - "Review Focus"
Cohesion: 0.25
Nodes (8): Global Constraints, Out of scope, P5.5 iPad Feature Parity Implementation Plan, Review Focus, Task 1: Rust locations module, stops filter, airport changes, Task 2: CheapWingsKit — selections, filter, itinerary info, Task 3: App — airport picker, filter, itinerary details, Task 4: Phase close

### Community 162 - "CheapWings — Worker Implementation Handoff"
Cohesion: 0.12
Nodes (16): Authorized task boundaries, Preserve current baseline, 08 — Starting Prompt for a Local Coding Agent, Implementation invariants, Single reporting location, Dated history is evidence rather than active instructions, Documentation precedence, CheapWings — Worker Implementation Handoff (+8 more)

### Community 163 - "skiplagged.rs"
Cohesion: 0.12
Nodes (25): Card, cards(), completeness(), days_from_civil(), decimal_text(), decode_card(), fli_source_offer(), FxNote (+17 more)

### Community 164 - "Foundation"
Cohesion: 0.10
Nodes (12): FliProbe, FliWreq, RustCore, SizeApp, .body, SizeApp, .body, SizeApp (+4 more)

### Community 165 - "drain"
Cohesion: 0.18
Nodes (12): test_airport_change_never_claims_ground_cost_is_known_on_reprice(), reprice(), search(), test_skiplagged_names_stay_summary_metadata_without_invented_flights(), test_surface_change_and_carriers_survive_worker_storage_api(), search(), zones(), CheckingFake (+4 more)

### Community 167 - "build_location_catalog.py"
Cohesion: 0.22
Nodes (3): compute_fingerprint(), test_frozen_cross_language_engine_fixtures(), build()

### Community 168 - "LocalInstant"
Cohesion: 0.50
Nodes (4): fingerprint(), fp::LocalInstant, LocalInstant, Segment

### Community 169 - "Theme.swift"
Cohesion: 0.12
Nodes (15): .accessibilityText, .priceText, .body, .content, .body, .price, CarrierPlate, .body (+7 more)

### Community 170 - "p46-browser.mjs"
Cohesion: 0.28
Nodes (6): all, dist, job, offer(), richEntries, trip()

### Community 172 - "SearchStore"
Cohesion: 0.13
Nodes (16): StoreTests, SearchStore, Final review (fresh subagent, Opus), Next, Owner-found crash and the continued-processing decision, P5.3 — iPad persistence and resume, Global Constraints, Out of scope (+8 more)

### Community 173 - "MCPReply"
Cohesion: 0.13
Nodes (10): TransportError, notHTTP, tooLarge, MCPError, badReply, http, MCPReply, MCPTransport (+2 more)

### Community 176 - ".lane"
Cohesion: 0.16
Nodes (5): LanePause, .remaining, RunEmitter, StopFlag, .isSet

### Community 177 - "05 — Web + Native iOS Client Implementation"
Cohesion: 0.29
Nodes (7): 05 — Web + Native iOS Client Implementation, Polling and recovery design, Web first iOS second, Native SwiftUI implementation plan, Web and SwiftUI share remote search engine, P5 native iOS gate, Native SwiftUI P5

### Community 178 - "Money"
Cohesion: 0.19
Nodes (6): Money, test_cannot_compare_different_currencies(), test_idr_has_zero_minor_units(), test_money_rejects_float(), test_money_requires_known_currency_for_minor_units(), test_usd_has_two_minor_units()

### Community 179 - "parity.py"
Cohesion: 0.32
Nodes (3): check(), py_convert(), same()

### Community 180 - "PlanError"
Cohesion: 0.18
Nodes (16): civil_from_days(), days_from_civil(), format_date(), normalize(), parse_date(), plan_search(), PlanError, DatesReversed (+8 more)

### Community 181 - "P6 — Release acceptance"
Cohesion: 0.18
Nodes (10): Live provider canary, Live web Fli acceptance, Local transport diagnostics, Offline checkpoint, Open release items, Owner-approved Fli retry, P6 — Release acceptance, Paired live transport check (+2 more)

### Community 182 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:browser

### Community 183 - "ComboStatus"
Cohesion: 0.33
Nodes (4): ComboStatus, Done, Failed, Pending

### Community 184 - "subprocess"
Cohesion: 0.22
Nodes (7): test_generator_money_reference_runs_without_rust_core(), test_beyond_96_bit_raises_instead_of_rounding(), Behaviour changes, Not in P5.1 (next phases), P5.1 — Shared Rust core, Verification (fresh runs at phase close), What exists now

### Community 185 - "toolReply"
Cohesion: 0.38
Nodes (3): RoutingMCPTransport, Sent, toolReply()

### Community 186 - "Implementation checklist and gates"
Cohesion: 0.29
Nodes (7): 1. Correct documentation and record the plan, 2. Connect existing Rust engine rules to Python, 3. Connect Fli and Skiplagged parsing, Deferred work, Design and boundaries, Implementation checklist and gates, P5.7 — Move the web backend onto the shared Rust core

### Community 187 - "browser.mjs"
Cohesion: 0.33
Nodes (3): capabilities, dist, job

### Community 188 - "Pre-restructure WORK_LOG header (baseline, full tracker, ledger, summary, deviations)"
Cohesion: 0.22
Nodes (8): Canonical evidence-preserving extensions, Pre-restructure WORK_LOG header (baseline, full tracker, ledger, summary, deviations), 2026-11-09 empty-repo baseline, Historical initial repository and toolchain, Pre-restructure phase summary, FlightFinder renamed CheapWings, Owner acceptance and merge4c98386, Merged P4.11 baseline

### Community 189 - "XCTestCase"
Cohesion: 0.29
Nodes (4): coreRevisionError(), verifyCoreRevision(), CoreRevisionTests, cheapwings_ffiFFI

### Community 191 - "SearchEngine"
Cohesion: 0.05
Nodes (28): FetchedPage, isAllowedFliRedirect(), RedirectPolicy, .refused, URLSessionFliTransport, PriceText, SearchEngine, PriceTextTests (+20 more)

### Community 192 - "Review Focus"
Cohesion: 0.29
Nodes (7): Global Constraints, Out of scope (later phases), P5.1 Shared Rust Core Implementation Plan, Review Focus, Task 2: Fingerprint and ranking, Task 3: Fli `tfs` encoder and `ds:1` page decoder, Task 6: Phase close

### Community 193 - "p45-browser.mjs"
Cohesion: 0.33
Nodes (5): baseJob, commonOffer, dist, itinerary, query

### Community 195 - "P5.4 — Skiplagged on the iPad"
Cohesion: 0.33
Nodes (6): Final review (fresh subagent, Opus), Next, P5.4 — Skiplagged on the iPad, Rulings made during implementation, Verification, What exists now

### Community 196 - "provider_probe_swoop.py"
Cohesion: 0.53
Nodes (4): main(), run(), _to_jsonable(), _utc_now_iso()

### Community 197 - "ProbeResult"
Cohesion: 0.22
Nodes (9): FliProbe, ProbeResult, .summary, UserAgentMode, chromeDesktop, .header, safariIOS, safariIPad (+1 more)

### Community 199 - "P5.5 — iPad feature parity"
Cohesion: 0.33
Nodes (6): Final review (fresh subagent, Opus), Next, P5.5 — iPad feature parity, Picker UX (owner decision during the device check), Rulings made during implementation, Verification

### Community 200 - "skiplagged_cases"
Cohesion: 0.50
Nodes (3): skiplagged_cases(), case(), text()

### Community 201 - "dependencies"
Cohesion: 0.50
Nodes (4): dependencies, react@^19.3.1, react-dom@^19.3.1, react-dom

### Community 202 - "NetworkMonitor"
Cohesion: 0.22
Nodes (7): NetworkMonitor, Final review (fresh subagent, Opus), Next, P5.6 — iPad polish, Rulings made during implementation, Verification, What exists now

### Community 204 - "OfferDetailView"
Cohesion: 0.12
Nodes (12): Array, Step, airport, change, flight, layover, summary, StepRow (+4 more)

### Community 207 - "test_p57_engine.py"
Cohesion: 0.18
Nodes (7): fold(), LocationCatalog, MajorResolution, MajorSelection, test_fold_matches_assigned_python_unicode(), location_major_cases(), case()

### Community 209 - "money-pyo3/src/lib.rs"
Cohesion: 0.21
Nodes (8): as_minor_units(), cheapwings_money_rs(), exponent(), EXPONENTS, from_minor_units(), fx_convert(), minor_unit_exponent(), parse()

### Community 214 - "fli-wreq/src/lib.rs"
Cohesion: 0.21
Nodes (7): MAX_BODY, wreq_fetch(), WreqError, Build, Request, TooLarge, WreqResponse

### Community 215 - "StopReason"
Cohesion: 0.06
Nodes (22): .isGoogleStop, Date, .milliseconds, .isProviderStop, .storedText, StopReason, backgrounded, blocked (+14 more)

### Community 217 - "deserialize"
Cohesion: 0.39
Nodes (5): fingerprint(), isoformat(), LocalInstant, Segment, isoformat_matches_python_shapes()

## Knowledge Gaps
- **256 isolated node(s):** `.description`, `partialPayload`, `schemaChanged`, `Error`, `Resolved` (+251 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1282 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **45 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `P4.12 — Shared global resource pool` connect `BoundedCall` to `react`, `WORK_LOG.md — Current State (keep under ~80 lines)`, `Repository`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._
- **Are the 47 inferred relationships involving `ProviderFailure` (e.g. with `JobRunner` and `ExactCapture`) actually correct?**
  _`ProviderFailure` has 47 INFERRED edges - model-reasoned connections that need verification._
- **What connects `.description`, `partialPayload`, `schemaChanged` to the rest of the system?**
  _256 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `JobRunner` be split into smaller, more focused modules?**
  _Cohesion score 0.09151138716356108 - nodes in this community are weakly interconnected._
- **Why does `Search-status visualization (2026-11-12)` connect `react` to `BoundedCall`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
- **Are the 88 inferred relationships involving `Repository` (e.g. with `AirportTransfer` and `IdentityConfidence`) actually correct?**
  _`Repository` has 88 INFERRED edges - model-reasoned connections that need verification._
- **Should `Sendable` be split into smaller, more focused modules?**
  _Cohesion score 0.12096774193548387 - nodes in this community are weakly interconnected._