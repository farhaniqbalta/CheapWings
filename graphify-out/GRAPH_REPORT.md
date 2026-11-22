# Graph Report - CheapWings-p7  (2026-11-22)

## Corpus Check
- 357 files · ~543,432 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 30 file(s) not represented in the graph (top: (none) 16, .jsonl 6, .css 3)

## Summary
- 4029 nodes · 10290 edges · 225 communities (173 shown, 52 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 1769 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `413c2b27`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_scheduler.py
- Sendable
- src/discovery_sources.rs
- OctotripProvider
- test_p49_review.py
- SearchEvent
- base
- 06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria
- P46ResultsWorkspace.tsx
- rust/src/lib.rs
- test_fli.py
- ProviderPacing
- App.tsx
- cache.py
- 04 — Data, Persistence, and REST API Contracts
- P5.7 — Execution evidence
- P4.5 UI/UX handover, intake and fixes
- base
- test_p57_parsers.py
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
- p412-browser.mjs
- compilerOptions
- P4.10 — Smart location selection
- SearchQuery
- View
- Repository
- RouteDate
- BoundedCall
- P4.11 — Fli as a fourth provider
- repository.py
- SwiftCore
- WorkStatus
- CheapWings — P7 Explore Anywhere / Discover
- View
- P7 Discover — Readiness, Feasibility and Shared Rust Core Implementation Plan
- Theme.swift
- FliOffer
- SourceOffer
- cheapwings-ffi/src/lib.rs
- .testParallelStopLeavesUnreleasedPendingForResume
- MCPClient
- .oxlintrc.json
- gen_fixtures.py
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
- Money
- FakeClock
- test_api.py
- test_octotrip.py
- P4.9 — Scheduler architecture, implementation and verification
- 19. Python Tech Stack Decision, Long-Running Jobs, and Cross-Platform Integration
- P4.8 — Provider interval benchmark and scheduling plan (2026-11-10)
- FlightFinder — Architecture & Design Review Handoff
- 17. Mandatory Multi-Provider Aggregation Architecture (restored; mandatory)
- 12. MVP Milestones and Checkpoints
- catalog
- DaySummary
- 18. Web + Native iOS Product Design
- 1. Product Intent, Requirements, and Non-Goals
- 2. Proposed Search Experience / UX
- 3. Candidate Data Sources and Due-Diligence Notes
- 15. Mandatory Deliverables from the Reviewing Agent
- 5. Search Algorithm, Coverage, and Failure Handling
- 6. Fare Data Model & Comparability
- .application
- 11. Minimal Test Plan and Evaluation Matrix
- 20. Mandatory Cross-Platform and Multi-Provider Acceptance Tests
- 4. Architecture Proposal
- 7. Price Verification Policy
- 8. Filtering and Travel Risks
- AGENTS.md
- CLAUDE.md
- fixtures.rs
- cheapwings-py/src/lib.rs
- swoop.py
- 03 — Provider Feasibility, Multi-Provider Aggregation, and Fare Accuracy
- FliError
- AirlineNames
- Tfs
- ItineraryInfo
- ProbeView
- test_core_fixtures.py
- Fli probe — P5.06 spikes S1 (iPhone) and S3 (Swift off-device)
- SearchRequest
- money.rs
- P7.4 Discover runtime Implementation Plan
- FixtureTests
- fli-wreq/build.sh
- fli-wreq
- json
- cheapwings-money-rs
- cheapwings-money-rs
- providers/fli.py
- LocationCatalog
- test_overlap_429_retry_after_and_independent_provider
- fli-wreq/src/lib.rs
- batch
- ranking.rs
- gen_core_fixtures.py
- StoreError
- expand_routes_and_dates
- CheapWings
- build-ios.sh
- rust/build.sh
- ResumeTests
- core-s5
- SearchModel
- shadow_money.py
- P5.06 — Native engine spikes (S1–S5)
- cheapwings-core/src/lib.rs
- cheapwings-core
- cheapwings-ffi
- cheapwings-py
- asyncio
- CheapWingsCore
- cheapwings-store/src/lib.rs
- money-pyo3/src/lib.rs
- StatusVisuals.tsx
- p412_report.py
- catalog
- Outcome
- CoreError
- cheapwings-core
- ProviderFailure
- Review Focus
- Current phase tracker and owner approvals
- skiplagged.rs
- View
- src/discovery.rs
- UnknownCurrencyError
- LocalInstant
- .start
- p46-browser.mjs
- source-revision.sh
- provider_probe_skiplagged.py
- parity.py
- update-expected-revision.sh
- .lane
- utc
- tests/discovery.rs
- LocationTests
- PlanError
- P6 — Release acceptance
- scripts
- .body
- create_app
- SearchEngine
- Decodable
- browser.mjs
- Review Focus
- XCTestCase
- PackageDescription
- FetchedPage
- skiplagged_cases
- pytest
- P7.1 — Discovery provider feasibility
- MajorSelection
- references/query.py
- ProbeResult
- LocationCatalog
- gen_discovery_sources_fixtures.py
- MajorSelection
- Implementation checklist and gates
- P5.1 — Shared Rust core
- p45-browser.mjs
- OfferDetailView
- tfs
- 08 — Starting Prompt for a Local Coding Agent
- SkiplaggedError
- P5.5 — iPad feature parity
- references/expansion.py
- P7.2 / P7.3: Discover contract and shared Rust selection
- dependencies
- provider_probe_swoop.py
- DispatchDeferred
- DiscoveryObservation
- UserAgentMode
- Foundation
- fingerprint.rs
- ComboStatus
- SearchProvider

## God Nodes (most connected - your core abstractions)
1. `ProviderFailure` - 117 edges
2. `Repository` - 113 edges
3. `FakeProvider` - 94 edges
4. `Registration` - 94 edges
5. `JobRunner` - 67 edges
6. `SearchSession` - 67 edges
7. `WORK_LOG.md — Current State (keep under ~80 lines)` - 48 edges
8. `Offer` - 47 edges
9. `SearchModel` - 46 edges
10. `SearchQuery` - 44 edges

## Surprising Connections (you probably didn't know these)
- `Evidence (2026-11-21, worktree `CheapWings-p7`)` --references--> `DiscoveryFixtureTests`  [INFERRED]
  docs/log/p7.3.md → apps/ios/CheapWingsCore/Tests/CheapWingsCoreTests/DiscoveryFixtureTests.swift
- `Task 2: Bindings for Task 1 (iPad first, then Python)` --references--> `DiscoveryFixtureTests`  [INFERRED]
  docs/log/p7.4-plan.md → apps/ios/CheapWingsCore/Tests/CheapWingsCoreTests/DiscoveryFixtureTests.swift
- `Task 4: `SkiplaggedDiscoveryProvider` (Swift)` --references--> `MCPTransport`  [INFERRED]
  docs/log/p7.4-plan.md → apps/ios/CheapWingsKit/Sources/CheapWingsKit/MCPClient.swift
- `Global Constraints` --references--> `PacedRunner`  [INFERRED]
  docs/log/p5.4-plan.md → apps/ios/CheapWingsKit/Sources/CheapWingsKit/PacedRunner.swift
- `1. Actual repository state and migration dependency` --references--> `PacedRunner`  [INFERRED]
  docs/log/p7-handover.md → apps/ios/CheapWingsKit/Sources/CheapWingsKit/PacedRunner.swift

## Import Cycles
- 1-file cycle: `core/cheapwings-core/src/skiplagged.rs -> core/cheapwings-core/src/skiplagged.rs`

## Hyperedges (group relationships)
- **Planned SwiftUI shares backend contract and durable recovery** — docs_05_web_and_native_ios_swiftui_plan, docs_06_implementation_checkpoints_p5, readme_ios_planned [EXTRACTED 1.00]
- **Exact identity, exact money and unknown-safe rankings** — docs_03_providers_aggregation_pricing_itinerary_offer_identity, docs_03_providers_aggregation_pricing_decimal_money_fx, docs_01_product_requirements_ux_safe_and_advertised_rankings, docs_04_data_and_api_contracts_three_valued_unknowns [INFERRED 0.85]
- **Canonical fare evidence remains conservative across adapters and clients** — docs_03_providers_aggregation_pricing_money, docs_04_data_and_api_contracts_three_valued, docs_log_p4_11_fare_limits, readme_safe_ranking [INFERRED 0.95]

## Communities (225 total, 52 thin omitted)

### Community 0 - "test_scheduler.py"
Cohesion: 0.10
Nodes (38): DispatchFailure, JobRunner, test_fli_real_normalization_api_prices_and_cache(), transport(), test_missing_fli_payload_is_failure_and_never_cached(), Logged, test_blocking_adapter_pool_sized_to_g_uses_real_threads(), search() (+30 more)

### Community 1 - "Sendable"
Cohesion: 0.13
Nodes (8): Decoded, DecodeError, .description, partialPayload, schemaChanged, Leg, Offer, Page

### Community 2 - "src/discovery_sources.rs"
Cohesion: 0.13
Nodes (22): DiscoveryObservation, DiscoveryQuery, FxRate, anywhere_web_payload(), AnywhereInput, AnywherePage, calls_web_payload(), discovery_calls() (+14 more)

### Community 3 - "OctotripProvider"
Cohesion: 0.19
Nodes (6): OctotripProvider, HttpStartGate, test_octotrip_429_stops_unsent_peer_http(), test_octotrip_gate_covers_initialization_across_three_sessions(), respond(), test_unsupported_filters_do_not_call_transport()

### Community 4 - "test_p49_review.py"
Cohesion: 0.20
Nodes (17): ReviewDispatcher, ReviewRepository, TimedFake, drain(), max_overlap(), query(), test_cooldown_occupies_no_execution_slot(), test_database_failure_surfaces_instead_of_silent_worker_loss() (+9 more)

### Community 5 - "SearchEvent"
Cohesion: 0.12
Nodes (19): SearchEvent, comboFailed, item, offers, offersHidden, progress, providerStopped, started (+11 more)

### Community 6 - "base"
Cohesion: 0.06
Nodes (34): CODE_SIGN_STYLE, CURRENT_PROJECT_VERSION, GENERATE_INFOPLIST_FILE, INFOPLIST_KEY_UILaunchScreen_Generation, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPad, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPhone, MARKETING_VERSION, PRODUCT_BUNDLE_IDENTIFIER (+26 more)

### Community 7 - "06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria"
Cohesion: 0.09
Nodes (20): Bounded blocking provider execution, API application domain dependency boundaries, Dependency boundary, 02 — System Architecture and Runtime Boundaries, Capability-driven provider abstraction, Provider capability protocols, Native SwiftUI implementation plan, 06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria (+12 more)

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
Cohesion: 0.10
Nodes (20): FliSearchProvider, FliTransport, PacedRunner, ProviderPacing, InFlightCounter, SlowFakeProvider, Final review (fresh subagent, Opus), Next (+12 more)

### Community 12 - "App.tsx"
Cohesion: 0.13
Nodes (23): api, ApiError, BASE_URL, request(), TERMINAL_STATUSES, errorMessage(), getOwnerToken(), setOwnerToken() (+15 more)

### Community 13 - "cache.py"
Cohesion: 0.23
Nodes (5): cache_key(), CacheRepository, without_handles(), OperationAttempt, recent_job_start()

### Community 14 - "04 — Data, Persistence, and REST API Contracts"
Cohesion: 0.09
Nodes (22): Scheduler design requirements, Same-offer exact repricing, Authentication and secret boundary, Canonical Money Itinerary Offer Coverage, Coverage and terminal statuses, 04 — Data, Persistence, and REST API Contracts, Normative versioned REST design, Normative versioned REST v1 and canonical DTOs (+14 more)

### Community 15 - "P5.7 — Execution evidence"
Cohesion: 0.14
Nodes (14): Baseline and checkpoint 1 — 2026-11-18, Checkpoint 2 — engine/PyO3, 2026-11-18, Checkpoint 3 — Fli and Skiplagged parsing, Decisions and review, Execution decisions, Offline verification, P5.7 — Execution evidence, PR #21 review update (+6 more)

### Community 16 - "P4.5 UI/UX handover, intake and fixes"
Cohesion: 0.09
Nodes (25): Canonical evidence-preserving extensions, Pre-restructure WORK_LOG header (baseline, full tracker, ledger, summary, deviations), 2026-11-09 empty-repo baseline, Historical initial repository and toolchain, Pre-restructure phase summary, FlightFinder renamed CheapWings, P2–P4 implementation log, Historical CGK to CTS cancelled review (+17 more)

### Community 17 - "base"
Cohesion: 0.05
Nodes (37): ASSETCATALOG_COMPILER_APPICON_NAME, CODE_SIGN_STYLE, CURRENT_PROJECT_VERSION, GENERATE_INFOPLIST_FILE, INFOPLIST_KEY_CFBundleDisplayName, INFOPLIST_KEY_UILaunchScreen_Generation, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPad, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPhone (+29 more)

### Community 18 - "test_p57_parsers.py"
Cohesion: 0.27
Nodes (6): Clock, outcome(), require_fli(), test_fli_complete_result_parity(), test_recorded_fli_page(), test_skiplagged_complete_result_parity()

### Community 19 - "WORK_LOG.md — Current State (keep under ~80 lines)"
Cohesion: 0.13
Nodes (15): 05 — Web + Native iOS Client Implementation, Polling and recovery design, Web first iOS second, Web and SwiftUI share remote search engine, Evidence and phase-history index, 2026-11-11 documentation cleanup, Documentation precedence, CheapWings — Worker Implementation Handoff (+7 more)

### Community 20 - "Provider and result-cache research (2026-11-10)"
Cohesion: 0.06
Nodes (33): request_snapshot(), Cache and OctoTrip implementation kickoff (2026-11-10), Current code audit — implications for caching, Dated provider evaluation — primary sources, not production approval, Final live acceptance and handover — cache + OctoTrip, Hosted endpoint preflight — actual observations and limits, Implementation checkpoint — durable cache and backend selection (in progress), Live owner search — cross-provider overlap confirmed (2026-11-10) (+25 more)

### Community 21 - "Experiment"
Cohesion: 0.12
Nodes (8): Experiment, post(), wrap(), observed(), test_octotrip_three_sessions_share_one_http_gate(), session(), test_response_timing_preserves_stream_bytes(), respond()

### Community 22 - "SearchSession"
Cohesion: 0.03
Nodes (58): NetworkMonitor, .isGoogleStop, StoreTests, Date, .milliseconds, SearchPersistence, SearchStore, .isProviderStop (+50 more)

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
Cohesion: 0.15
Nodes (6): GateTransport, Outcome, error, page, ParallelPacingTests, SleepGate

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
Cohesion: 0.12
Nodes (15): ResultsExpired, 10. Sources, facts and open questions, 1. Executive verdict, 2. Provider compatibility matrix, 3. Native engine design and module ownership, 4. Port-vs-drop matrix, 5. Background / foreground behaviour (iOS), 6. Risk register (likelihood × impact, 1–5) (+7 more)

### Community 31 - "test_search_cache.py"
Cohesion: 0.12
Nodes (35): _exact_reprice_count(), status_projection(), FareQuote, ProviderResultCache, test_airport_change_never_claims_ground_cost_is_known_on_reprice(), reprice(), search(), test_skiplagged_names_stay_summary_metadata_without_invented_flights() (+27 more)

### Community 32 - "p412-browser.mjs"
Cohesion: 0.17
Nodes (9): playwright@^1.65.0, dist, evidence, shots, dist, dist, job, pool (+1 more)

### Community 33 - "compilerOptions"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 34 - "P4.10 — Smart location selection"
Cohesion: 0.11
Nodes (22): Airportsdata and mwgg Airports MIT attribution, MIT airport data license, Airportsdata and mwgg Airports MIT attribution, MIT airport data license, Exhaustive combination coverage, P4.10 historical offline acceptance, Backend authoritative Major resolution, Typed Major backend authority (+14 more)

### Community 36 - "View"
Cohesion: 0.10
Nodes (19): AirportPicker, .body, AirportToggleRow, ChipLabelStyle, PlaceAirports, .body, PlaceLink, PlaceRow (+11 more)

### Community 37 - "Repository"
Cohesion: 0.10
Nodes (45): Registration, write_session(), ProviderState, WorkAttempt, now_ms(), Repository, test_surface_change_and_carriers_survive_worker_storage_api(), zones() (+37 more)

### Community 38 - "RouteDate"
Cohesion: 0.18
Nodes (10): combo_from_store(), plan_search(), PlanSearchError, Rejected, route_from_core(), route_to_core(), RouteDate, store::StoredRequest (+2 more)

### Community 39 - "BoundedCall"
Cohesion: 0.07
Nodes (22): BoundedCall, __init__(), test_bounded_swoop_executor_c3_has_actual_overlap_and_no_queue(), __init__(), __init__(), __init__(), test_real_thread_slot_retained_on_cancellation(), 1. Architecture review — P4.9 admission as merged (+14 more)

### Community 40 - "P4.11 — Fli as a fourth provider"
Cohesion: 0.11
Nodes (19): Historical usable quote verification, P4.11 — Fli as a fourth provider, Truthful failure and cache semantics, Fourth provider Fli public Google Flights page, P4.11 acceptance evidence, Explicit HTTP2 transport, Indicative Google quotes and generic search links, Historical HTTP2 live measurements (+11 more)

### Community 41 - "repository.py"
Cohesion: 0.05
Nodes (38): instant(), public_offer(), results_projection(), airport_transfers(), AirportTransfer, compute_fingerprint(), IdentityConfidence, Itinerary (+30 more)

### Community 42 - "SwiftCore"
Cohesion: 0.21
Nodes (8): FingerprintCase, Fixtures, Instant, MoneyCase, Offer, RankingCase, Segment, SwiftCore

### Community 43 - "WorkStatus"
Cohesion: 0.14
Nodes (18): main(), run_demo(), CoverageEntry, unique_covered_combinations(), build_itinerary(), ItineraryGroup, MatchEngine, best_checked_deal() (+10 more)

### Community 44 - "CheapWings — P7 Explore Anywhere / Discover"
Cohesion: 0.11
Nodes (18): 0. Read this first — non-negotiable owner intent, 10. Required agent output before coding, 1. Actual repository state and migration dependency, 2.1 Inputs, 2.2 Output and sorting, 2.3 Honest coverage, 2. Product definition, 3.1 Existing vs new responsibilities (+10 more)

### Community 45 - "View"
Cohesion: 0.13
Nodes (15): .body, SelectedMark, .body, CheapWingsApp, .body, RouteHeader, .arrow, .body (+7 more)

### Community 46 - "P7 Discover — Readiness, Feasibility and Shared Rust Core Implementation Plan"
Cohesion: 0.17
Nodes (12): Global Constraints, Out of this plan (next plans, after P7.1 go), P7 Discover — Readiness, Feasibility and Shared Rust Core Implementation Plan, Phase A — P7.0 / P7.1 (docs and probe; no product code), Phase B — P7.2 / P7.3 (shared Rust core), Review Focus, Task 2: P7.1 desk feasibility matrix, Task 3: P7.1 approved probe and go/no-go (+4 more)

### Community 47 - "Theme.swift"
Cohesion: 0.14
Nodes (9): RustCore, SizeApp, .body, SizeApp, .body, SizeApp, .body, SwiftCore (+1 more)

### Community 48 - "FliOffer"
Cohesion: 0.13
Nodes (25): airport_changes(), CheckedOffers, cross_check(), currency_from_token(), decode_page(), extract_ds1(), filter_offers(), FliLeg (+17 more)

### Community 49 - "SourceOffer"
Cohesion: 0.20
Nodes (10): AirportChange, fli_airport_changes(), fli_source_offer(), FliLeg, FliOffer, FxNote, leg_from_core(), leg_to_core() (+2 more)

### Community 50 - "cheapwings-ffi/src/lib.rs"
Cohesion: 0.11
Nodes (18): AnywherePage, best_checked_deal(), cheapwings_core_build_revision(), core_query(), discovery_calls(), DiscoveryCall, DiscoveryCounts, DiscoveryPlan (+10 more)

### Community 52 - "MCPClient"
Cohesion: 0.05
Nodes (35): MCPClient, MCPError, badReply, http, MCPReply, MCPTransport, URLSessionMCPTransport, SkiplaggedFetch (+27 more)

### Community 53 - ".oxlintrc.json"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 54 - "gen_fixtures.py"
Cohesion: 0.16
Nodes (10): parse_search_response(), search(), test_guard_keeps_sdk_priced_offer_construction(), test_missing_or_malformed_payload_is_not_empty_success(), test_short_rpc_error_is_not_empty_success(), test_valid_empty_with_metadata_frame_is_preserved(), fingerprint_cases(), instant() (+2 more)

### Community 55 - "contracts.py"
Cohesion: 0.13
Nodes (21): capabilities(), create_search(), worker_pool(), AirportTransfer, Capabilities, Coverage, Created, DTO (+13 more)

### Community 56 - "FliPage"
Cohesion: 0.22
Nodes (8): fli_cross_check(), fli_decode_page(), fli_filter_offers(), fli::FliPage, FliCheckedOffers, FliDecodeError, Failed, FliPage

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

### Community 77 - "Money"
Cohesion: 0.16
Nodes (9): Money, test_unknown_currency_raises_unknown_currency_error(), test_cannot_compare_different_currencies(), test_fx_snapshot_converts(), test_idr_has_zero_minor_units(), test_money_rejects_float(), test_money_requires_known_currency_for_minor_units(), test_usd_has_two_minor_units() (+1 more)

### Community 78 - "FakeClock"
Cohesion: 0.20
Nodes (6): FakeClock, .sleep, .sleeps, FakeTransport, page(), SearchEngineTests

### Community 79 - "test_api.py"
Cohesion: 0.11
Nodes (35): FakeProvider, ScriptedOutcome, client_for(), request_data(), test_api_scheduler_results_contract(), test_auth_and_remote_boundary(), test_baggage_eligibility_and_snapshot_cursor(), test_capabilities_report_default_source_selection() (+27 more)

### Community 80 - "test_octotrip.py"
Cohesion: 0.18
Nodes (9): payload(), query(), test_bad_source_values_fail_or_disable_navigation(), test_mcp_returns_on_matching_event_without_waiting_for_stream_close(), test_neighbor_airports_are_excluded_and_elapsed_time_includes_layover(), test_rpc_sse_decimal_decode_and_429(), handler(), test_summary_is_honest_and_money_and_source_metadata_retained() (+1 more)

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

### Community 87 - "catalog"
Cohesion: 0.28
Nodes (7): catalog(), plan_scope(), test_catalog_preserves_complete_records_and_order(), test_catalog_unicode_casefold_matches_reference(), test_invalid_ranking_amount_raises(), test_python_whitespace_semantics_for_catalog_and_scope(), test_scope_preview_matches_reference()

### Community 88 - "DaySummary"
Cohesion: 0.07
Nodes (27): DateRibbon, .body, DayColumn, .accessibilityText, .background, .bar, .body, .date (+19 more)

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
Nodes (37): airport_lookup_has_timezone(), catalog(), CATALOG, FingerprintCase, Fixtures, fixtures(), FIXTURES, fli_pages_match_python() (+29 more)

### Community 106 - "cheapwings-py/src/lib.rs"
Cohesion: 0.10
Nodes (20): as_minor_units(), catalog_error(), cheapwings_core(), discovery_calls(), fingerprint(), fli_extract_ds1(), fli_parse(), from_minor_units() (+12 more)

### Community 107 - "swoop.py"
Cohesion: 0.07
Nodes (36): PublicOffer, shortlist(), WorkStatus, _core_call(), minor_unit_exponent(), ComparisonStatus, LinkScope, PriceStatus (+28 more)

### Community 108 - "03 — Provider Feasibility, Multi-Provider Aggregation, and Fare Accuracy"
Cohesion: 0.09
Nodes (25): Accessible responsive UI, 01 — Product Requirements, Rules, and UX Acceptance, One-way adult economy flight finder, Flexible one-way finder scope, Query coverage differs from inventory completeness, Conservative fare ranking, Safe Best checked and Lowest advertised views, Honest results states (+17 more)

### Community 109 - "FliError"
Cohesion: 0.23
Nodes (12): decode_row(), FliError, AuthDenied, PartialPayload, SchemaChanged, local_time(), page_rows(), RawLeg (+4 more)

### Community 110 - "AirlineNames"
Cohesion: 0.11
Nodes (10): OfferRow, .codesLine, .detailLine, .flights, .hasLegs, .spoken, .stopsText, AirlineNames (+2 more)

### Community 112 - "ItineraryInfo"
Cohesion: 0.15
Nodes (4): .summary, ItineraryInfo, Layover, ItineraryInfoTests

### Community 113 - "ProbeView"
Cohesion: 0.15
Nodes (7): WreqProbe, FliProbeApp, .body, ProbeView, .body, S5Section, .body

### Community 114 - "test_core_fixtures.py"
Cohesion: 0.18
Nodes (8): test_generator_money_reference_runs_without_rust_core(), _python_api_result(), test_beyond_28_digits_is_exact(), test_beyond_96_bit_raises_instead_of_rounding(), test_missing_core_module_names_the_fix(), test_money_fixtures_through_python_api(), Behaviour changes, Task 4: Python backend uses Rust money (PyO3)

### Community 115 - "Fli probe — P5.06 spikes S1 (iPhone) and S3 (Swift off-device)"
Cohesion: 0.33
Nodes (5): Fli probe — P5.06 spikes S1 (iPhone) and S3 (Swift off-device), Offline check (no network), S1 — physical iPhone (needs full Xcode, owner-approved live requests), S3 — Swift off-device (macOS pre-check), What this does not do

### Community 116 - "SearchRequest"
Cohesion: 0.15
Nodes (3): .stored, SearchRequest, .country

### Community 117 - "money.rs"
Cohesion: 0.18
Nodes (13): as_minor_units(), EXPONENTS, from_minor_units(), fx_convert(), minor_unit_exponent(), MoneyError, InvalidDecimal, NotWholeMinorUnits (+5 more)

### Community 118 - "P7.4 Discover runtime Implementation Plan"
Cohesion: 0.13
Nodes (13): P7.4: Discover runtime, Global Constraints, Out of this plan, P7.4 Discover runtime Implementation Plan, PR A: shared core, PR C: web runtime, Review Focus, Task 10: API and status projection (+5 more)

### Community 119 - "FixtureTests"
Cohesion: 0.11
Nodes (22): FingerprintCase, Fixtures, FixtureTests, InstantJ, LegJ, MoneyCase, OfferExpectJ, OfferJ (+14 more)

### Community 120 - "fli-wreq/build.sh"
Cohesion: 0.33
Nodes (5): DEVELOPER_DIR, IPHONEOS_DEPLOYMENT_TARGET, MACOSX_DEPLOYMENT_TARGET, PATH, build.sh script

### Community 124 - "json"
Cohesion: 0.04
Nodes (33): upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), payload() (+25 more)

### Community 127 - "providers/fli.py"
Cohesion: 0.06
Nodes (11): _codes(), compute_fingerprint(), test_fingerprint_matches_frozen_reference(), test_fixture_generators_do_not_call_rust_engine(), test_frozen_cross_language_engine_fixtures(), test_anywhere_case(), test_discovery_calls_case(), test_bad_json_is_value_error() (+3 more)

### Community 128 - "LocationCatalog"
Cohesion: 0.16
Nodes (6): CatalogError, Failed, Location, LocationCatalog, MajorResolution, SearchPage

### Community 129 - "test_overlap_429_retry_after_and_independent_provider"
Cohesion: 0.18
Nodes (15): claim(), engine(), migrate(), reg(), drain(), record(), short(), recover() (+7 more)

### Community 130 - "fli-wreq/src/lib.rs"
Cohesion: 0.21
Nodes (7): MAX_BODY, wreq_fetch(), WreqError, Build, Request, TooLarge, WreqResponse

### Community 131 - "batch"
Cohesion: 0.07
Nodes (9): batch(), emit(), peak(), percentile(), Pool, MeasuredProduction, quantile(), run_trial() (+1 more)

### Community 132 - "ranking.rs"
Cohesion: 0.31
Nodes (8): best_checked_deal(), ExactAmount, lowest_advertised(), priced(), RankOffer, tier(), validate_amount(), ranking_matches_python()

### Community 133 - "gen_core_fixtures.py"
Cohesion: 0.16
Nodes (19): currency_token(), expected_offer(), fingerprint_cases(), fli_leg(), fli_page_cases(), fli_row(), fli_tfs_cases(), instant() (+11 more)

### Community 134 - "StoreError"
Cohesion: 0.17
Nodes (8): HiddenCount, ProviderStop, SearchStore, StoredCombo, StoredOffer, StoredSearch, StoreError, Failed

### Community 135 - "expand_routes_and_dates"
Cohesion: 0.42
Nodes (7): expand_routes_and_dates(), RouteDateCombo, _query(), test_1x3x9_expands_to_27_combinations(), test_combos_are_unique_and_deterministic_order(), test_duplicate_input_codes_are_deduplicated_before_expansion(), test_same_origin_destination_pair_is_skipped()

### Community 136 - "CheapWings"
Cohesion: 0.10
Nodes (27): Synthetic browser regressions, CheapWings web, React TypeScript Vite thin client, Runtime private access, Memory-only web owner token, Intercepted Playwright browser regression suite, React Vite thin client, Durable job and work state (+19 more)

### Community 137 - "build-ios.sh"
Cohesion: 0.33
Nodes (5): DEVELOPER_DIR, IPHONEOS_DEPLOYMENT_TARGET, MACOSX_DEPLOYMENT_TARGET, PATH, build-ios.sh script

### Community 138 - "rust/build.sh"
Cohesion: 0.33
Nodes (5): DEVELOPER_DIR, IPHONEOS_DEPLOYMENT_TARGET, MACOSX_DEPLOYMENT_TARGET, PATH, build.sh script

### Community 139 - "ResumeTests"
Cohesion: 0.11
Nodes (7): FoundOffer, .providerID, .shownPrice, sourceOffer(), ResumeTests, Tfs, Task 2: Session checkpointing and resume (CheapWingsKit)

### Community 142 - "SearchModel"
Cohesion: 0.08
Nodes (8): .dayShift, SearchModel, .canResume, .canSearch, .plan, .planSummary, .searchTitle, .selectedSources

### Community 144 - "shadow_money.py"
Cohesion: 0.23
Nodes (6): pytest_configure(), as_minor_units(), convert(), from_minor_units(), minor_unit_exponent(), _shadow()

### Community 145 - "P5.06 — Native engine spikes (S1–S5)"
Cohesion: 0.40
Nodes (5): Decision status, Owner decision (2026-11-13, after S5), P5.06 — Native engine spikes (S1–S5), Reproduce, S5 — Rust core vs Swift core on iPad (follow-up, same day)

### Community 150 - "asyncio"
Cohesion: 0.14
Nodes (18): lifespan(), Settings, default_registry(), database(), require_current_schema(), main(), worker_lock(), test_fourth_registration_configuration_and_no_false_capabilities() (+10 more)

### Community 151 - "CheapWingsCore"
Cohesion: 0.15
Nodes (4): SearchProvider, CheapWingsCore, CheapWingsKit, XCTest

### Community 152 - "cheapwings-store/src/lib.rs"
Cohesion: 0.06
Nodes (41): RouteDate, FxNote, SourceOffer, ComboStatus, Done, Failed, Pending, from_json() (+33 more)

### Community 153 - "money-pyo3/src/lib.rs"
Cohesion: 0.26
Nodes (8): as_minor_units(), cheapwings_money_rs(), exponent(), EXPONENTS, from_minor_units(), fx_convert(), minor_unit_exponent(), parse()

### Community 154 - "StatusVisuals.tsx"
Cohesion: 0.27
Nodes (10): ProviderProgress, WorkerPool, LABEL, P46SearchProgress(), PoolGauge(), ProviderBars(), SEGMENTS, SOURCE_NAMES (+2 more)

### Community 155 - "p412_report.py"
Cohesion: 0.48
Nodes (4): cell(), fmt(), load(), main()

### Community 156 - "catalog"
Cohesion: 0.25
Nodes (11): plan_scope(), catalog(), selection(), test_ambiguous_cities_keep_distinct_ids_and_geography(), test_boundary_and_overlap_match_expansion(), test_catalog_rejects_inconsistent_data(), test_lookup(), test_major_resolution_and_no_fallback() (+3 more)

### Community 157 - "Outcome"
Cohesion: 0.17
Nodes (12): Outcome, blockedRedirect, blockedSorry, blockedTraffic, crossCheckFailed, httpError, .mustStop, networkError (+4 more)

### Community 158 - "CoreError"
Cohesion: 0.29
Nodes (6): as_minor_units(), CoreError, Invalid, from_minor_units(), fx_convert(), minor_unit_exponent()

### Community 160 - "ProviderFailure"
Cohesion: 0.06
Nodes (42): ProviderFailure, SourceEvidence, ItinerarySummary, FXSnapshot, Offer, ProviderRepriceResult, ProviderSearchResult, aware_iso() (+34 more)

### Community 161 - "Review Focus"
Cohesion: 0.25
Nodes (8): Global Constraints, Out of scope, P5.5 iPad Feature Parity Implementation Plan, Review Focus, Task 1: Rust locations module, stops filter, airport changes, Task 2: CheapWingsKit — selections, filter, itinerary info, Task 3: App — airport picker, filter, itinerary details, Task 4: Phase close

### Community 162 - "Current phase tracker and owner approvals"
Cohesion: 0.29
Nodes (7): Dated history is evidence rather than active instructions, Current documentation authority, Compact current work-log template, WORK_LOG.md — Current State Template, Initialization-only work-log template, Current phase tracker and owner approvals, Planned SwiftUI iOS requires full Xcode

### Community 163 - "skiplagged.rs"
Cohesion: 0.18
Nodes (20): Card, cards(), completeness(), days_from_civil(), decimal_text(), decode_card(), naive_parts(), skiplagged_link() (+12 more)

### Community 164 - "View"
Cohesion: 0.13
Nodes (13): .priceText, .body, .body, .price, CarrierPlate, .body, CarriersLine, .body (+5 more)

### Community 165 - "src/discovery.rs"
Cohesion: 0.20
Nodes (11): BUDGET_HEADROOM, code(), DiscoveryError, InvalidBudget, InvalidCurrency, Plan, select_discovery_plan(), Survivor (+3 more)

### Community 167 - "UnknownCurrencyError"
Cohesion: 0.22
Nodes (7): UnknownCurrencyError, Global Constraints, Out of scope (later phases), P5.1 Shared Rust Core Implementation Plan, Review Focus, Task 2: Fingerprint and ranking, Task 6: Phase close

### Community 168 - "LocalInstant"
Cohesion: 0.50
Nodes (4): fingerprint(), fp::LocalInstant, LocalInstant, Segment

### Community 169 - ".start"
Cohesion: 0.18
Nodes (3): .offer, DaySummaryTests, SearchSessionTests

### Community 170 - "p46-browser.mjs"
Cohesion: 0.28
Nodes (6): all, dist, job, offer(), richEntries, trip()

### Community 172 - "provider_probe_skiplagged.py"
Cohesion: 0.27
Nodes (5): main(), _redact(), run(), run_calls(), _utc_now_iso()

### Community 173 - "parity.py"
Cohesion: 0.47
Nodes (3): check(), py_convert(), same()

### Community 176 - ".lane"
Cohesion: 0.13
Nodes (7): LanePause, .remaining, RunEmitter, StopFlag, .isSet, BackgroundTasks, os

### Community 177 - "utc"
Cohesion: 0.20
Nodes (6): Measurements, observers(), make_send(), observed(), post(), utc()

### Community 178 - "tests/discovery.rs"
Cohesion: 0.18
Nodes (17): DiscoveryCounts, DiscoveryPlan, SelectedLead, Case, cases(), check(), check_named(), empty_input_is_empty_plan() (+9 more)

### Community 179 - "LocationTests"
Cohesion: 0.15
Nodes (8): Expect, error, ids, Fixtures, LocationTests, MajorCase, MajorExpect, SearchCase

### Community 180 - "PlanError"
Cohesion: 0.17
Nodes (16): civil_from_days(), days_from_civil(), format_date(), normalize(), parse_date(), plan_search(), PlanError, DatesReversed (+8 more)

### Community 181 - "P6 — Release acceptance"
Cohesion: 0.20
Nodes (10): Live provider canary, Live web Fli acceptance, Local transport diagnostics, Offline checkpoint, Open release items, Owner-approved Fli retry, P6 — Release acceptance, Paired live transport check (+2 more)

### Community 182 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:browser

### Community 183 - ".body"
Cohesion: 0.31
Nodes (5): ResultsView, .body, .session, SearchSession.Phase, .stopMessage

### Community 184 - "create_app"
Cohesion: 0.18
Nodes (6): create_app(), cancel(), get_job(), get_results(), health(), resolve_location()

### Community 185 - "SearchEngine"
Cohesion: 0.07
Nodes (23): URLSessionFliTransport, PriceText, SearchEngine, PriceTextTests, Behaviour and limits, Final review (fresh subagent, Opus), Next, Owner test on the fixed build — all-rows-rejected bug (2026-11-14) (+15 more)

### Community 186 - "Decodable"
Cohesion: 0.19
Nodes (19): CaseJ, CountsJ, DiscoveryFixtureTests, ExpectJ, Fixtures, FxJ, LeadJ, ObservationJ (+11 more)

### Community 187 - "browser.mjs"
Cohesion: 0.33
Nodes (3): capabilities, dist, job

### Community 188 - "Review Focus"
Cohesion: 0.25
Nodes (8): Design direction (frontend-design pass, owner request 2026-11-14), Global Constraints, Out of scope, P5.6 iPad Polish Implementation Plan, Review Focus, Task 2: Picker speed and correctness (P5.5 deferred minors), Task 3: Visual design, VoiceOver, larger text, dark mode, narrow windows, Task 4: Phase close

### Community 189 - "XCTestCase"
Cohesion: 0.29
Nodes (4): coreRevisionError(), verifyCoreRevision(), CoreRevisionTests, cheapwings_ffiFFI

### Community 191 - "FetchedPage"
Cohesion: 0.09
Nodes (9): FetchedPage, isAllowedFliRedirect(), RedirectPolicy, .refused, TransportError, notHTTP, tooLarge, OfflineErrors (+1 more)

### Community 192 - "skiplagged_cases"
Cohesion: 0.50
Nodes (3): skiplagged_cases(), case(), text()

### Community 193 - "pytest"
Cohesion: 0.49
Nodes (8): _base(), test_include_hidden_city_defaults_false_and_does_not_silently_flip(), test_rejects_excessive_combination_count(), test_rejects_invalid_iata(), test_rejects_multi_adult_in_mvp(), test_rejects_reversed_dates(), test_rejects_roundtrip_in_mvp(), test_rejects_same_origin_and_destination()

### Community 194 - "P7.1 — Discovery provider feasibility"
Cohesion: 0.18
Nodes (11): Desk matrix (no provider calls made), Detailed check (`sk_flights_search`, `sort=price`), Exact-date bridge (Skiplagged), Fli Explore addendum (owner-approved, 2026-11-21), Go / no-go, Limitations, P7.1 — Discovery provider feasibility, Probe request (needs owner approval) (+3 more)

### Community 195 - "MajorSelection"
Cohesion: 0.25
Nodes (3): LocationCatalog, MajorResolution, MajorSelection

### Community 197 - "ProbeResult"
Cohesion: 0.23
Nodes (6): Results, Task 3: Fli `tfs` encoder and `ds:1` page decoder, FliProbe, isAllowedRedirect(), ProbeResult, .summary

### Community 198 - "LocationCatalog"
Cohesion: 0.32
Nodes (3): fold(), LocationCatalog, test_fold_matches_assigned_python_unicode()

### Community 200 - "MajorSelection"
Cohesion: 0.38
Nodes (5): MajorResolution, MajorSelection, test_catalog_major_messages_and_order(), location_major_cases(), case()

### Community 201 - "Implementation checklist and gates"
Cohesion: 0.29
Nodes (7): 1. Correct documentation and record the plan, 2. Connect existing Rust engine rules to Python, 3. Connect Fli and Skiplagged parsing, Deferred work, Design and boundaries, Implementation checklist and gates, P5.7 — Move the web backend onto the shared Rust core

### Community 202 - "P5.1 — Shared Rust core"
Cohesion: 0.33
Nodes (6): test_core_module_is_rust(), Not in P5.1 (next phases), P5.1 — Shared Rust core, Rulings made during implementation, Verification (fresh runs at phase close), What exists now

### Community 203 - "p45-browser.mjs"
Cohesion: 0.33
Nodes (5): baseJob, commonOffer, dist, itinerary, query

### Community 204 - "OfferDetailView"
Cohesion: 0.11
Nodes (15): Array, OfferDetailView, .steps, Step, airport, change, flight, layover (+7 more)

### Community 205 - "tfs"
Cohesion: 0.47
Nodes (6): length_delimited(), search_url(), tfs(), varint(), varint_field(), fli_tfs_matches_python()

### Community 206 - "08 — Starting Prompt for a Local Coding Agent"
Cohesion: 0.33
Nodes (5): Authorized task boundaries, Preserve current baseline, 08 — Starting Prompt for a Local Coding Agent, Implementation invariants, Single reporting location

### Community 207 - "SkiplaggedError"
Cohesion: 0.33
Nodes (5): skiplagged_parse(), skiplagged_tool_payload(), SkiplaggedError, Failed, SkiplaggedPage

### Community 208 - "P5.5 — iPad feature parity"
Cohesion: 0.33
Nodes (6): Final review (fresh subagent, Opus), Next, P5.5 — iPad feature parity, Picker UX (owner decision during the device check), Rulings made during implementation, Verification

### Community 210 - "P7.2 / P7.3: Discover contract and shared Rust selection"
Cohesion: 0.40
Nodes (5): Evidence (2026-11-21, worktree `CheapWings-p7`), Limitations, Owner decisions (Task 4 gate, 2026-11-21), P7.2 / P7.3: Discover contract and shared Rust selection, What exists now

### Community 211 - "dependencies"
Cohesion: 0.50
Nodes (4): dependencies, react@^19.3.1, react-dom@^19.3.1, react-dom

### Community 212 - "provider_probe_swoop.py"
Cohesion: 0.53
Nodes (4): main(), run(), _to_jsonable(), _utc_now_iso()

### Community 215 - "UserAgentMode"
Cohesion: 0.33
Nodes (6): UserAgentMode, chromeDesktop, .header, safariIOS, safariIPad, system

### Community 216 - "Foundation"
Cohesion: 0.18
Nodes (5): CryptoKit, FliProbe, FliWreq, Foundation, SelfTest

### Community 217 - "fingerprint.rs"
Cohesion: 0.29
Nodes (6): fingerprint(), isoformat(), LocalInstant, Segment, fingerprint_matches_python(), isoformat_matches_python_shapes()

### Community 222 - "ComboStatus"
Cohesion: 0.50
Nodes (4): ComboStatus, Done, Failed, Pending

## Knowledge Gaps
- **257 isolated node(s):** `NoAirports`, `DatesReversed`, `TooMany`, `SchemaChanged`, `InvalidPrice` (+252 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1365 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **52 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SearchSession` connect `SearchSession` to `Sendable`, `.start`, `repository.py`, `ResumeTests`, `ProviderPacing`, `SearchModel`, `P7 Discover — Readiness, Feasibility and Shared Rust Core Implementation Plan`, `MCPClient`, `.body`, `SearchEngine`?**
  _High betweenness centrality (0.163) - this node is a cross-community bridge._
- **Are the 48 inferred relationships involving `ProviderFailure` (e.g. with `JobRunner` and `ExactCapture`) actually correct?**
  _`ProviderFailure` has 48 INFERRED edges - model-reasoned connections that need verification._
- **What connects `NoAirports`, `DatesReversed`, `TooMany` to the rest of the system?**
  _257 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_scheduler.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10163934426229508 - nodes in this community are weakly interconnected._
- **Why does `P4.12 — Shared global resource pool` connect `BoundedCall` to `StatusVisuals.tsx`, `WORK_LOG.md — Current State (keep under ~80 lines)`, `Repository`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._
- **Are the 88 inferred relationships involving `Repository` (e.g. with `AirportTransfer` and `IdentityConfidence`) actually correct?**
  _`Repository` has 88 INFERRED edges - model-reasoned connections that need verification._
- **Should `Sendable` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._