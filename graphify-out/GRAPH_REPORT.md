# Graph Report - CheapWings-p7  (2026-11-22)

## Corpus Check
- 361 files · ~547,912 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 30 file(s) not represented in the graph (top: (none) 16, .jsonl 6, .css 3)

## Summary
- 4157 nodes · 10688 edges · 239 communities (175 shown, 64 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 1830 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f2fefa54`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_scheduler.py
- Sendable
- tests/discovery_sources.rs
- FakeProvider
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
- DiscoveryOutcome
- WORK_LOG.md — Current State (keep under ~80 lines)
- Provider and result-cache research (2026-11-10)
- p48_throughput.py
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
- p46-browser.mjs
- compilerOptions
- P4.10 — Smart location selection
- pytest
- View
- Repository
- plan_search
- SwoopProvider
- P4.11 — Fli as a fourth provider
- FlightSegment
- SwiftCore
- WorkStatus
- CheapWings — P7 Explore Anywhere / Discover
- View
- P7 Discover — Readiness, Feasibility and Shared Rust Core Implementation Plan
- Theme.swift
- FliOffer
- DiscoverySessionTests
- cheapwings-ffi/src/lib.rs
- .testParallelStopLeavesUnreleasedPendingForResume
- MCPClient
- .oxlintrc.json
- datetime
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
- fake.py
- 03 — Provider Feasibility, Multi-Provider Aggregation, and Fare Accuracy
- p49_scheduler_comparison.py
- AirlineNames
- Tfs
- ItineraryInfo
- store.rs
- test_core_fixtures.py
- Fli probe — P5.06 spikes S1 (iPhone) and S3 (Swift off-device)
- SearchRequest
- money.rs
- EmptyOutcome
- FixtureTests
- fli-wreq/build.sh
- fli-wreq
- repository.py
- cheapwings-money-rs
- cheapwings-money-rs
- test_p57_engine.py
- LocationCatalog
- test_overlap_429_retry_after_and_independent_provider
- fli-wreq/src/lib.rs
- run_trial
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
- StoreError
- money-pyo3/src/lib.rs
- reply
- p412_pool_benchmark.py
- catalog
- Outcome
- CoreError
- cheapwings-core
- ProviderFailure
- Review Focus
- CheapWings — Worker Implementation Handoff
- skiplagged.rs
- View
- src/discovery.rs
- UnknownCurrencyError
- LocalInstant
- .start
- .restoreLatest
- source-revision.sh
- provider_probe_skiplagged.py
- money.py
- update-expected-revision.sh
- .lane
- utc
- tests/discovery.rs
- LocationTests
- PlanError
- P6 — Release acceptance
- SearchStore
- .body
- routes.py
- StopReason
- Decodable
- cheapwings-store/tests/discovery.rs
- NetworkMonitor
- XCTestCase
- cheapwings-store/src/lib.rs
- FetchedPage
- skiplagged_cases
- SearchPersistence
- P7.1 — Discovery provider feasibility
- SkiplaggedSearchProvider
- references/query.py
- p2_smoke.py
- references/catalog.py
- json
- DayColumn
- Implementation checklist and gates
- P4.12 — Shared global resource pool
- .discover
- OfferDetailView
- RoutingMCPTransport
- WorkStatus
- SourceOffer
- P5.5 — iPad feature parity
- references/expansion.py
- P7.2 / P7.3: Discover contract and shared Rust selection
- MCPTransport
- .testGoogleStopHoldsFliButSkiplaggedResumesNow
- 05 — Web + Native iOS Client Implementation
- DiscoverySnapshot
- .execute
- Foundation
- fingerprint.rs
- P5.2 — iPad app shell
- ComboStatus
- SearchProvider
- FXSnapshot
- P5.4 — Skiplagged on the iPad
- Fli 0.25 s interval reliability (owner request, 2026-11-14)
- search

## God Nodes (most connected - your core abstractions)
1. `ProviderFailure` - 117 edges
2. `Repository` - 113 edges
3. `Registration` - 94 edges
4. `FakeProvider` - 94 edges
5. `SearchSession` - 80 edges
6. `JobRunner` - 67 edges
7. `WORK_LOG.md — Current State (keep under ~80 lines)` - 48 edges
8. `Offer` - 47 edges
9. `SearchModel` - 46 edges
10. `FakeClock` - 46 edges

## Surprising Connections (you probably didn't know these)
- `Rulings made during implementation` --references--> `SearchPersistence`  [INFERRED]
  docs/log/p5.3.md → apps/ios/CheapWingsKit/Sources/CheapWingsKit/Persistence.swift
- `Rulings made during implementation` --references--> `FoundOffer`  [INFERRED]
  docs/log/p5.2.md → apps/ios/CheapWingsKit/Sources/CheapWingsKit/SearchEngine.swift
- `Final review (fresh subagent, Opus)` --references--> `SearchSession`  [INFERRED]
  docs/log/p5.2.md → apps/ios/CheapWingsKit/Sources/CheapWingsKit/SearchSession.swift
- `Verification` --references--> `SearchSession`  [INFERRED]
  docs/log/p5.2.md → apps/ios/CheapWingsKit/Sources/CheapWingsKit/SearchSession.swift
- `Out of this plan (next plans, after P7.1 go)` --references--> `SearchSession`  [INFERRED]
  docs/log/p7-plan.md → apps/ios/CheapWingsKit/Sources/CheapWingsKit/SearchSession.swift

## Import Cycles
- 1-file cycle: `core/cheapwings-core/src/skiplagged.rs -> core/cheapwings-core/src/skiplagged.rs`

## Hyperedges (group relationships)
- **Planned SwiftUI shares backend contract and durable recovery** — docs_05_web_and_native_ios_swiftui_plan, docs_06_implementation_checkpoints_p5, readme_ios_planned [EXTRACTED 1.00]
- **Exact identity, exact money and unknown-safe rankings** — docs_03_providers_aggregation_pricing_itinerary_offer_identity, docs_03_providers_aggregation_pricing_decimal_money_fx, docs_01_product_requirements_ux_safe_and_advertised_rankings, docs_04_data_and_api_contracts_three_valued_unknowns [INFERRED 0.85]
- **Canonical fare evidence remains conservative across adapters and clients** — docs_03_providers_aggregation_pricing_money, docs_04_data_and_api_contracts_three_valued, docs_log_p4_11_fare_limits, readme_safe_ranking [INFERRED 0.95]

## Communities (239 total, 64 thin omitted)

### Community 0 - "test_scheduler.py"
Cohesion: 0.09
Nodes (55): JobRunner, Registration, test_fli_real_normalization_api_prices_and_cache(), transport(), test_fli_uses_durable_shared_fetch_cancel_fencing_and_cache(), test_missing_fli_payload_is_failure_and_never_cached(), test_short_source_expiry_preserves_other_source_and_running_job(), Logged (+47 more)

### Community 1 - "Sendable"
Cohesion: 0.13
Nodes (8): Decoded, DecodeError, .description, partialPayload, schemaChanged, Leg, Offer, Page

### Community 2 - "tests/discovery_sources.rs"
Cohesion: 0.23
Nodes (10): DiscoveryCall, anywhere_fixture_cases(), AnywhereCase, AnywhereExpect, CallsCase, CallsExpect, discovery_call_cases(), Fixtures (+2 more)

### Community 3 - "FakeProvider"
Cohesion: 0.17
Nodes (19): SingleDateRouteQuery, FakeProvider, ScriptedOutcome, test_api_scheduler_results_contract(), test_safe_external_link_policy(), sample(), test_octotrip_429_stops_unsent_peer_http(), test_octotrip_gate_covers_initialization_across_three_sessions() (+11 more)

### Community 4 - "test_p49_review.py"
Cohesion: 0.22
Nodes (17): ReviewDispatcher, ReviewRepository, TimedFake, drain(), max_overlap(), query(), test_cooldown_occupies_no_execution_slot(), test_database_failure_surfaces_instead_of_silent_worker_loss() (+9 more)

### Community 5 - "SearchEvent"
Cohesion: 0.13
Nodes (15): SearchEvent, comboFailed, item, offers, offersHidden, progress, providerStopped, started (+7 more)

### Community 6 - "base"
Cohesion: 0.06
Nodes (34): CODE_SIGN_STYLE, CURRENT_PROJECT_VERSION, GENERATE_INFOPLIST_FILE, INFOPLIST_KEY_UILaunchScreen_Generation, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPad, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPhone, MARKETING_VERSION, PRODUCT_BUNDLE_IDENTIFIER (+26 more)

### Community 7 - "06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria"
Cohesion: 0.11
Nodes (17): Bounded blocking provider execution, API application domain dependency boundaries, Dependency boundary, 02 — System Architecture and Runtime Boundaries, Capability-driven provider abstraction, Provider capability protocols, 06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria, Fundamental incompatibility escalation (+9 more)

### Community 8 - "P46ResultsWorkspace.tsx"
Cohesion: 0.15
Nodes (27): PublicOffer, FareRiskNotice(), formatDuration(), ItineraryCard(), BAG_LABEL, COMPARISON_LABEL, describeLink(), OfferList() (+19 more)

### Community 9 - "rust/src/lib.rs"
Cohesion: 0.18
Nodes (22): as_minor_units(), best_checked_deal(), exponent(), EXPONENTS, fingerprint(), FingerprintCase, Fixtures, from_minor_units() (+14 more)

### Community 10 - "test_fli.py"
Cohesion: 0.21
Nodes (14): payload(), provider(), query(), test_c3_real_threads_overlap_and_cancel_retains_physical_capacity(), fetch(), test_challenge_redirect_is_not_followed(), test_exact_prices_identity_and_conservative_evidence(), test_fetch_pins_http2_and_preserves_json_price_lexemes() (+6 more)

### Community 11 - "ProviderPacing"
Cohesion: 0.06
Nodes (36): FliSearchProvider, FliTransport, PacedRunner, OfflineErrors, ProviderOutcome, failed, found, retry (+28 more)

### Community 12 - "App.tsx"
Cohesion: 0.13
Nodes (24): api, ApiError, BASE_URL, request(), TERMINAL_STATUSES, errorMessage(), getOwnerToken(), setOwnerToken() (+16 more)

### Community 13 - "cache.py"
Cohesion: 0.18
Nodes (5): cache_key(), CacheRepository, without_handles(), ProviderOperation, recent_job_start()

### Community 14 - "04 — Data, Persistence, and REST API Contracts"
Cohesion: 0.09
Nodes (22): Scheduler design requirements, Same-offer exact repricing, Authentication and secret boundary, Canonical Money Itinerary Offer Coverage, Coverage and terminal statuses, 04 — Data, Persistence, and REST API Contracts, Normative versioned REST design, Normative versioned REST v1 and canonical DTOs (+14 more)

### Community 15 - "P5.7 — Execution evidence"
Cohesion: 0.14
Nodes (14): Baseline and checkpoint 1 — 2026-11-18, Checkpoint 2 — engine/PyO3, 2026-11-18, Checkpoint 3 — Fli and Skiplagged parsing, Decisions and review, Execution decisions, Offline verification, P5.7 — Execution evidence, PR #21 review update (+6 more)

### Community 16 - "P4.5 UI/UX handover, intake and fixes"
Cohesion: 0.08
Nodes (27): Itinerary versus seller offer, Canonical evidence-preserving extensions, Pre-restructure WORK_LOG header (baseline, full tracker, ledger, summary, deviations), 2026-11-09 empty-repo baseline, Historical initial repository and toolchain, Pre-restructure phase summary, FlightFinder renamed CheapWings, P2–P4 implementation log (+19 more)

### Community 17 - "base"
Cohesion: 0.05
Nodes (37): ASSETCATALOG_COMPILER_APPICON_NAME, CODE_SIGN_STYLE, CURRENT_PROJECT_VERSION, GENERATE_INFOPLIST_FILE, INFOPLIST_KEY_CFBundleDisplayName, INFOPLIST_KEY_UILaunchScreen_Generation, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPad, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPhone (+29 more)

### Community 18 - "DiscoveryOutcome"
Cohesion: 0.12
Nodes (11): DiscoveryOutcome, failed, page, retry, stop, DiscoveryProvider, SkiplaggedDiscoveryProvider, Date (+3 more)

### Community 19 - "WORK_LOG.md — Current State (keep under ~80 lines)"
Cohesion: 0.17
Nodes (7): Evidence and phase-history index, 2026-11-11 documentation cleanup, Approved deviations, WORK_LOG.md — Current State (keep under ~80 lines), Current next task, Owner-controlled publication, Personal-use provider decisions

### Community 20 - "Provider and result-cache research (2026-11-10)"
Cohesion: 0.06
Nodes (32): request_snapshot(), Cache and OctoTrip implementation kickoff (2026-11-10), Dated provider evaluation — primary sources, not production approval, Final live acceptance and handover — cache + OctoTrip, Hosted endpoint preflight — actual observations and limits, Implementation checkpoint — durable cache and backend selection (in progress), Live owner search — cross-provider overlap confirmed (2026-11-10), Offline cache/OctoTrip acceptance checkpoint (+24 more)

### Community 21 - "p48_throughput.py"
Cohesion: 0.07
Nodes (17): live_guard(), batch(), emit(), Experiment, post(), wrap(), observed(), main() (+9 more)

### Community 22 - "SearchSession"
Cohesion: 0.11
Nodes (7): ResumeInfo, SearchSession, .canResume, .doneSoFar, .isRunning, .pendingItems, .resumeAllowedAfter

### Community 23 - "types.ts"
Cohesion: 0.08
Nodes (27): AirportTransfer, ComparisonStatus, Coverage, ExpiredObservation, IdentityConfidence, Job, JobPhase, JobStatus (+19 more)

### Community 24 - "SearchForm.tsx"
Cohesion: 0.15
Nodes (18): Currency, ProviderCapability, AirportMultiSelect(), Props, Props, SearchForm(), todayIso(), createLocationService() (+10 more)

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
Cohesion: 0.08
Nodes (30): dependencies, react@^19.3.1, react-dom@^19.3.1, devDependencies, oxlint@^1.90.0, @types/node@^24.19.2, @types/react@^19.3.0, @types/react-dom@^19.3.0 (+22 more)

### Community 29 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 30 - "P5.05 — Native iOS search engine feasibility analysis"
Cohesion: 0.11
Nodes (19): 10. Sources, facts and open questions, 1. Executive verdict, 2. Provider compatibility matrix, 3. Native engine design and module ownership, 5. Background / foreground behaviour (iOS), 6. Risk register (likelihood × impact, 1–5), 7. Experiment plan (proposal; nothing run; each needs owner approval), 8. Architecture decision record (+11 more)

### Community 31 - "test_search_cache.py"
Cohesion: 0.09
Nodes (42): results_projection(), status_projection(), ProviderResultCache, test_pagination_freezes_incremental_quote_set(), payload(), test_airport_change_never_claims_ground_cost_is_known_on_reprice(), reprice(), search() (+34 more)

### Community 32 - "p46-browser.mjs"
Cohesion: 0.08
Nodes (23): playwright@^1.65.0, capabilities, dist, job, dist, evidence, shots, dist (+15 more)

### Community 33 - "compilerOptions"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 34 - "P4.10 — Smart location selection"
Cohesion: 0.11
Nodes (22): Airportsdata and mwgg Airports MIT attribution, MIT airport data license, Airportsdata and mwgg Airports MIT attribution, MIT airport data license, Exhaustive combination coverage, P4.10 historical offline acceptance, Backend authoritative Major resolution, Typed Major backend authority (+14 more)

### Community 35 - "pytest"
Cohesion: 0.15
Nodes (14): QueryValidationError, SearchQuery, plan_scope(), test_boundary_and_overlap_match_expansion(), test_zero_routes_and_date_changes(), _base(), test_include_hidden_city_defaults_false_and_does_not_silently_flip(), test_rejects_excessive_combination_count() (+6 more)

### Community 36 - "View"
Cohesion: 0.10
Nodes (19): AirportPicker, .body, AirportToggleRow, ChipLabelStyle, PlaceAirports, .body, PlaceLink, PlaceRow (+11 more)

### Community 37 - "Repository"
Cohesion: 0.08
Nodes (41): _exact_reprice_count(), write_session(), Base, FareQuote, FXRow, ItineraryRow, ProviderState, QuoteRevision (+33 more)

### Community 38 - "plan_search"
Cohesion: 0.67
Nodes (3): plan_search(), PlanSearchError, Rejected

### Community 39 - "SwoopProvider"
Cohesion: 0.09
Nodes (19): ProviderRepriceResult, obj_dict(), BoundedCall, SwoopProvider, test_bounded_swoop_executor_c3_has_actual_overlap_and_no_queue(), load(), query(), test_missing_zone_retains_unmatched_summary() (+11 more)

### Community 40 - "P4.11 — Fli as a fourth provider"
Cohesion: 0.11
Nodes (19): Historical usable quote verification, P4.11 — Fli as a fourth provider, Truthful failure and cache semantics, Fourth provider Fli public Google Flights page, P4.11 acceptance evidence, Explicit HTTP2 transport, Indicative Google quotes and generic search links, Historical HTTP2 live measurements (+11 more)

### Community 41 - "FlightSegment"
Cohesion: 0.10
Nodes (15): compute_fingerprint(), Itinerary, FlightSegment, RepriceRequest, offer_from_row(), segments(), test_display_names_do_not_change_itinerary_fingerprint(), test_explicit_airport_change_retains_flight_identity_without_fake_leg() (+7 more)

### Community 42 - "SwiftCore"
Cohesion: 0.21
Nodes (8): FingerprintCase, Fixtures, Instant, MoneyCase, Offer, RankingCase, Segment, SwiftCore

### Community 43 - "WorkStatus"
Cohesion: 0.11
Nodes (20): main(), run_demo(), CoverageEntry, unique_covered_combinations(), AirportTransfer, IdentityConfidence, build_itinerary(), ItineraryGroup (+12 more)

### Community 44 - "CheapWings — P7 Explore Anywhere / Discover"
Cohesion: 0.12
Nodes (17): 0. Read this first — non-negotiable owner intent, 10. Required agent output before coding, 2.1 Inputs, 2.2 Output and sorting, 2.3 Honest coverage, 2. Product definition, 3.1 Existing vs new responsibilities, 3. Target architecture — after completed P5.7 and P6 (+9 more)

### Community 45 - "View"
Cohesion: 0.18
Nodes (12): .body, SelectedMark, .body, RouteHeader, .arrow, .body, SearchView, .body (+4 more)

### Community 46 - "P7 Discover — Readiness, Feasibility and Shared Rust Core Implementation Plan"
Cohesion: 0.17
Nodes (12): Global Constraints, Out of this plan (next plans, after P7.1 go), P7 Discover — Readiness, Feasibility and Shared Rust Core Implementation Plan, Phase A — P7.0 / P7.1 (docs and probe; no product code), Phase B — P7.2 / P7.3 (shared Rust core), Review Focus, Task 2: P7.1 desk feasibility matrix, Task 3: P7.1 approved probe and go/no-go (+4 more)

### Community 47 - "Theme.swift"
Cohesion: 0.10
Nodes (10): RustCore, SizeApp, .body, SizeApp, .body, SizeApp, .body, S5Section (+2 more)

### Community 48 - "FliOffer"
Cohesion: 0.08
Nodes (42): airport_changes(), CheckedOffers, cross_check(), currency_from_token(), decode_page(), decode_row(), extract_ds1(), filter_offers() (+34 more)

### Community 49 - "DiscoverySessionTests"
Cohesion: 0.26
Nodes (3): DiscoverySessionTests, leads(), ScriptedDiscovery

### Community 50 - "cheapwings-ffi/src/lib.rs"
Cohesion: 0.10
Nodes (17): AirportChange, best_checked_deal(), cheapwings_core_build_revision(), DiscoveryCounts, DiscoveryPlan, fli_airport_changes(), fli_filter_offers(), fli_source_offer() (+9 more)

### Community 52 - "MCPClient"
Cohesion: 0.19
Nodes (6): MCPClient, MCPError, badReply, http, MCPReply, MCPConcurrencyTests

### Community 53 - ".oxlintrc.json"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 54 - "datetime"
Cohesion: 0.10
Nodes (10): airport_transfers(), airport_zone(), _airports(), parse_search_response(), search(), Clock, test_missing_or_malformed_payload_is_not_empty_success(), test_short_rpc_error_is_not_empty_success() (+2 more)

### Community 55 - "contracts.py"
Cohesion: 0.11
Nodes (24): capabilities(), create_search(), worker_pool(), AirportTransfer, Capabilities, Coverage, Created, DTO (+16 more)

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

### Community 77 - "Money"
Cohesion: 0.19
Nodes (6): Money, test_cannot_compare_different_currencies(), test_idr_has_zero_minor_units(), test_money_rejects_float(), test_money_requires_known_currency_for_minor_units(), test_usd_has_two_minor_units()

### Community 78 - "FakeClock"
Cohesion: 0.19
Nodes (6): FakeClock, .sleep, .sleeps, FakeTransport, page(), SearchEngineTests

### Community 79 - "test_api.py"
Cohesion: 0.17
Nodes (20): client_for(), request_data(), test_auth_and_remote_boundary(), test_baggage_eligibility_and_snapshot_cursor(), test_capabilities_report_default_source_selection(), test_invalid_input_no_job(), test_openapi_committed_and_response_shapes(), test_quota_and_cancel() (+12 more)

### Community 80 - "test_octotrip.py"
Cohesion: 0.12
Nodes (12): OctotripProvider, HttpStartGate, payload(), query(), test_bad_source_values_fail_or_disable_navigation(), test_mcp_returns_on_matching_event_without_waiting_for_stream_close(), test_neighbor_airports_are_excluded_and_elapsed_time_includes_layover(), test_rpc_sse_decimal_decode_and_429() (+4 more)

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
Cohesion: 0.09
Nodes (15): .bar, .offer, Side, destination, .id, origin, DaySummary, .id (+7 more)

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
Nodes (20): as_minor_units(), catalog_error(), cheapwings_core(), discovery_calls(), fingerprint(), fli_extract_ds1(), fli_parse(), from_minor_units() (+12 more)

### Community 107 - "fake.py"
Cohesion: 0.14
Nodes (22): shortlist(), ComparisonStatus, LinkScope, PriceStatus, ProviderErrorCode, ThreeValued, best_checked_deal(), _is_safe_for_default_ranking() (+14 more)

### Community 108 - "03 — Provider Feasibility, Multi-Provider Aggregation, and Fare Accuracy"
Cohesion: 0.10
Nodes (23): Accessible responsive UI, 01 — Product Requirements, Rules, and UX Acceptance, One-way adult economy flight finder, Flexible one-way finder scope, Query coverage differs from inventory completeness, Conservative fare ranking, Safe Best checked and Lowest advertised views, Honest results states (+15 more)

### Community 109 - "p49_scheduler_comparison.py"
Cohesion: 0.12
Nodes (9): main(), append_result(), main(), replay_latencies(), Scenario, scenarios(), main(), main() (+1 more)

### Community 110 - "AirlineNames"
Cohesion: 0.11
Nodes (9): OfferRow, .codesLine, .detailLine, .flights, .hasLegs, .stopsText, AirlineNames, Carrier (+1 more)

### Community 112 - "ItineraryInfo"
Cohesion: 0.16
Nodes (4): .spoken, ItineraryInfo, Layover, ItineraryInfoTests

### Community 113 - "store.rs"
Cohesion: 0.17
Nodes (17): combos(), failed_combo_keeps_its_code(), finish_combo_is_idempotent(), fli_offer(), offer(), open(), pending_lists_unfinished_in_order(), provider_stops_round_trip() (+9 more)

### Community 114 - "test_core_fixtures.py"
Cohesion: 0.16
Nodes (13): _python_api_result(), test_beyond_28_digits_is_exact(), test_beyond_96_bit_raises_instead_of_rounding(), test_core_module_is_rust(), test_missing_core_module_names_the_fix(), test_money_fixtures_through_python_api(), Behaviour changes, Not in P5.1 (next phases) (+5 more)

### Community 115 - "Fli probe — P5.06 spikes S1 (iPhone) and S3 (Swift off-device)"
Cohesion: 0.33
Nodes (5): Fli probe — P5.06 spikes S1 (iPhone) and S3 (Swift off-device), Offline check (no network), S1 — physical iPhone (needs full Xcode, owner-approved live requests), S3 — Swift off-device (macOS pre-check), What this does not do

### Community 116 - "SearchRequest"
Cohesion: 0.11
Nodes (9): .stored, Kind, discover, search, SearchRequest, .country, .discoveryQuery, PriceTextTests (+1 more)

### Community 117 - "money.rs"
Cohesion: 0.23
Nodes (13): as_minor_units(), EXPONENTS, from_minor_units(), fx_convert(), minor_unit_exponent(), MoneyError, InvalidDecimal, NotWholeMinorUnits (+5 more)

### Community 118 - "EmptyOutcome"
Cohesion: 0.07
Nodes (24): EmptyOutcome, formatChanged, noFlights, noneUnderBudget, noPrices, searchesFailed, sourceUnavailable, P7.4: Discover runtime (+16 more)

### Community 119 - "FixtureTests"
Cohesion: 0.11
Nodes (22): FingerprintCase, Fixtures, FixtureTests, InstantJ, LegJ, MoneyCase, OfferExpectJ, OfferJ (+14 more)

### Community 120 - "fli-wreq/build.sh"
Cohesion: 0.33
Nodes (5): DEVELOPER_DIR, IPHONEOS_DEPLOYMENT_TARGET, MACOSX_DEPLOYMENT_TARGET, PATH, build.sh script

### Community 124 - "repository.py"
Cohesion: 0.08
Nodes (14): upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), lifespan() (+6 more)

### Community 127 - "test_p57_engine.py"
Cohesion: 0.09
Nodes (6): compute_fingerprint(), test_fingerprint_matches_frozen_reference(), test_fixture_generators_do_not_call_rust_engine(), test_frozen_cross_language_engine_fixtures(), fingerprint_cases(), instant()

### Community 128 - "LocationCatalog"
Cohesion: 0.16
Nodes (6): CatalogError, Failed, Location, LocationCatalog, MajorResolution, SearchPage

### Community 129 - "test_overlap_429_retry_after_and_independent_provider"
Cohesion: 0.20
Nodes (15): reg(), drain(), record(), short(), recover(), test_concurrent_claims_under_real_sqlite_lock(), claim(), test_overlap_429_retry_after_and_independent_provider() (+7 more)

### Community 130 - "fli-wreq/src/lib.rs"
Cohesion: 0.21
Nodes (7): MAX_BODY, wreq_fetch(), WreqError, Build, Request, TooLarge, WreqResponse

### Community 132 - "ranking.rs"
Cohesion: 0.25
Nodes (9): best_checked_deal(), ExactAmount, lowest_advertised(), priced(), RankOffer, tier(), validate_amount(), ranking_matches_python() (+1 more)

### Community 133 - "gen_core_fixtures.py"
Cohesion: 0.18
Nodes (17): currency_token(), expected_offer(), fingerprint_cases(), fli_leg(), fli_page_cases(), fli_row(), fli_tfs_cases(), instant() (+9 more)

### Community 134 - "StoreError"
Cohesion: 0.11
Nodes (16): combo_from_store(), HiddenCount, items_to_store(), ProviderStop, route_from_core(), route_to_core(), RouteDate, SearchStore (+8 more)

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
Cohesion: 0.14
Nodes (6): FoundOffer, .providerID, .shownPrice, ResumeTests, Tfs, Task 2: Session checkpointing and resume (CheapWingsKit)

### Community 142 - "SearchModel"
Cohesion: 0.08
Nodes (8): .dayShift, SearchModel, .canResume, .canSearch, .plan, .planSummary, .searchTitle, .selectedSources

### Community 144 - "shadow_money.py"
Cohesion: 0.23
Nodes (6): pytest_configure(), as_minor_units(), convert(), from_minor_units(), minor_unit_exponent(), _shadow()

### Community 145 - "P5.06 — Native engine spikes (S1–S5)"
Cohesion: 0.29
Nodes (7): Decision status, Findings, Owner decision (2026-11-13, after S5), P5.06 — Native engine spikes (S1–S5), Reproduce, Results, S5 — Rust core vs Swift core on iPad (follow-up, same day)

### Community 150 - "asyncio"
Cohesion: 0.14
Nodes (12): DispatchDeferred, Settings, default_registry(), require_current_schema(), main(), worker_lock(), test_fourth_registration_configuration_and_no_false_capabilities(), test_missing_optional_fli_is_disabled_with_install_reason() (+4 more)

### Community 151 - "CheapWingsCore"
Cohesion: 0.16
Nodes (5): CheapWingsCore, CheapWingsKit, SwiftUI, UIKit, XCTest

### Community 152 - "StoreError"
Cohesion: 0.14
Nodes (14): from_json(), json(), sql(), Store, StoredCombo, StoredOffer, StoredRequest, StoredSearch (+6 more)

### Community 153 - "money-pyo3/src/lib.rs"
Cohesion: 0.20
Nodes (8): as_minor_units(), cheapwings_money_rs(), exponent(), EXPONENTS, from_minor_units(), fx_convert(), minor_unit_exponent(), parse()

### Community 154 - "reply"
Cohesion: 0.22
Nodes (6): FakeMCPTransport, MCPClientTests, reply(), SkiplaggedProviderTests, .combo, toolReply()

### Community 155 - "p412_pool_benchmark.py"
Cohesion: 0.15
Nodes (12): main(), peak(), quantile(), query(), scenario(), summarize(), threads(), cell() (+4 more)

### Community 156 - "catalog"
Cohesion: 0.16
Nodes (11): resolve_location(), catalog(), LocationCatalog, selection(), test_ambiguous_cities_keep_distinct_ids_and_geography(), test_catalog_rejects_inconsistent_data(), test_lookup(), test_major_resolution_and_no_fallback() (+3 more)

### Community 157 - "Outcome"
Cohesion: 0.12
Nodes (16): FliProbe, isAllowedRedirect(), Outcome, blockedRedirect, blockedSorry, blockedTraffic, crossCheckFailed, httpError (+8 more)

### Community 158 - "CoreError"
Cohesion: 0.29
Nodes (6): as_minor_units(), CoreError, Invalid, from_minor_units(), fx_convert(), minor_unit_exponent()

### Community 160 - "ProviderFailure"
Cohesion: 0.07
Nodes (34): ProviderFailure, SourceEvidence, ItinerarySummary, Offer, ProviderCapabilities, ProviderSearchResult, aware_iso(), decimal_value() (+26 more)

### Community 161 - "Review Focus"
Cohesion: 0.25
Nodes (8): Global Constraints, Out of scope, P5.5 iPad Feature Parity Implementation Plan, Review Focus, Task 1: Rust locations module, stops filter, airport changes, Task 2: CheapWingsKit — selections, filter, itinerary info, Task 3: App — airport picker, filter, itinerary details, Task 4: Phase close

### Community 162 - "CheapWings — Worker Implementation Handoff"
Cohesion: 0.12
Nodes (16): Authorized task boundaries, Preserve current baseline, 08 — Starting Prompt for a Local Coding Agent, Implementation invariants, Single reporting location, Dated history is evidence rather than active instructions, Documentation precedence, CheapWings — Worker Implementation Handoff (+8 more)

### Community 163 - "skiplagged.rs"
Cohesion: 0.16
Nodes (23): Card, cards(), completeness(), days_from_civil(), decimal_text(), decode_card(), fli_source_offer(), FxNote (+15 more)

### Community 164 - "View"
Cohesion: 0.15
Nodes (12): .priceText, .content, .body, CarrierPlate, .body, CarriersLine, .body, CompactPrice (+4 more)

### Community 165 - "src/discovery.rs"
Cohesion: 0.12
Nodes (23): BUDGET_HEADROOM, code(), DiscoveryError, InvalidBudget, InvalidCurrency, Plan, DiscoveryQuery, FxRate (+15 more)

### Community 167 - "UnknownCurrencyError"
Cohesion: 0.29
Nodes (7): Global Constraints, Out of scope (later phases), P5.1 Shared Rust Core Implementation Plan, Review Focus, Task 2: Fingerprint and ranking, Task 3: Fli `tfs` encoder and `ds:1` page decoder, Task 6: Phase close

### Community 168 - "LocalInstant"
Cohesion: 0.50
Nodes (4): fingerprint(), fp::LocalInstant, LocalInstant, Segment

### Community 170 - ".restoreLatest"
Cohesion: 0.12
Nodes (9): DiscoverySummary, Phase, idle, running, stopped, .emptyOutcome, SkippedSearch, Network (+1 more)

### Community 172 - "provider_probe_skiplagged.py"
Cohesion: 0.17
Nodes (6): build(), main(), _redact(), run(), run_calls(), _utc_now_iso()

### Community 173 - "money.py"
Cohesion: 0.18
Nodes (7): _core_call(), minor_unit_exponent(), UnknownCurrencyError, test_unknown_currency_raises_unknown_currency_error(), check(), py_convert(), same()

### Community 176 - ".lane"
Cohesion: 0.13
Nodes (7): LanePause, .remaining, RunEmitter, StopFlag, .isSet, BackgroundTasks, os

### Community 177 - "utc"
Cohesion: 0.14
Nodes (7): Measurements, ObservedProvider, observers(), make_send(), observed(), post(), utc()

### Community 178 - "tests/discovery.rs"
Cohesion: 0.18
Nodes (17): DiscoveryCounts, DiscoveryPlan, SelectedLead, Case, cases(), check(), check_named(), empty_input_is_empty_plan() (+9 more)

### Community 179 - "LocationTests"
Cohesion: 0.15
Nodes (8): Expect, error, ids, Fixtures, LocationTests, MajorCase, MajorExpect, SearchCase

### Community 180 - "PlanError"
Cohesion: 0.17
Nodes (17): civil_from_days(), days_from_civil(), format_date(), normalize(), parse_date(), plan_search(), PlanError, DatesReversed (+9 more)

### Community 181 - "P6 — Release acceptance"
Cohesion: 0.20
Nodes (10): Live provider canary, Live web Fli acceptance, Local transport diagnostics, Offline checkpoint, Open release items, Owner-approved Fli retry, P6 — Release acceptance, Paired live transport check (+2 more)

### Community 182 - "SearchStore"
Cohesion: 0.13
Nodes (16): StoreTests, SearchStore, Final review (fresh subagent, Opus), Next, Owner-found crash and the continued-processing decision, P5.3 — iPad persistence and resume, Global Constraints, Out of scope (+8 more)

### Community 183 - ".body"
Cohesion: 0.23
Nodes (7): CheapWingsApp, .body, ResultsView, .body, .session, SearchSession.Phase, .stopMessage

### Community 184 - "routes.py"
Cohesion: 0.08
Nodes (12): create_app(), cancel(), get_job(), get_results(), MajorResolution, MajorSelection, database(), CapacityExceeded (+4 more)

### Community 185 - "StopReason"
Cohesion: 0.07
Nodes (22): .isGoogleStop, .isProviderStop, .storedText, PriceText, rankLowestAdvertised(), SearchEngine, StopReason, backgrounded (+14 more)

### Community 186 - "Decodable"
Cohesion: 0.19
Nodes (19): CaseJ, CountsJ, DiscoveryFixtureTests, ExpectJ, Fixtures, FxJ, LeadJ, ObservationJ (+11 more)

### Community 187 - "cheapwings-store/tests/discovery.rs"
Cohesion: 0.22
Nodes (13): DiscoveryObservation, DiscoverySnapshot, commit_discovery_is_once(), commit_to_unknown_search_changes_nothing(), discover_request(), discovery_starts_without_items(), empty_commit_records_unavailable_discovery(), items() (+5 more)

### Community 188 - "NetworkMonitor"
Cohesion: 0.11
Nodes (16): NetworkMonitor, Final review (fresh subagent, Opus), Next, P5.6 — iPad polish, Design direction (frontend-design pass, owner request 2026-11-14), Global Constraints, Out of scope, P5.6 iPad Polish Implementation Plan (+8 more)

### Community 189 - "XCTestCase"
Cohesion: 0.29
Nodes (4): coreRevisionError(), verifyCoreRevision(), CoreRevisionTests, cheapwings_ffiFFI

### Community 190 - "cheapwings-store/src/lib.rs"
Cohesion: 0.11
Nodes (9): ComboStatus, Done, Failed, Pending, KEEP_SEARCHES, MIGRATE_V2, MIGRATE_V3, SCHEMA_V1 (+1 more)

### Community 191 - "FetchedPage"
Cohesion: 0.11
Nodes (9): FetchedPage, isAllowedFliRedirect(), RedirectPolicy, .refused, TransportError, notHTTP, tooLarge, URLSessionFliTransport (+1 more)

### Community 192 - "skiplagged_cases"
Cohesion: 0.40
Nodes (4): health(), skiplagged_cases(), case(), text()

### Community 194 - "P7.1 — Discovery provider feasibility"
Cohesion: 0.18
Nodes (11): Desk matrix (no provider calls made), Detailed check (`sk_flights_search`, `sort=price`), Exact-date bridge (Skiplagged), Fli Explore addendum (owner-approved, 2026-11-21), Go / no-go, Limitations, P7.1 — Discovery provider feasibility, Probe request (needs owner approval) (+3 more)

### Community 195 - "SkiplaggedSearchProvider"
Cohesion: 0.19
Nodes (4): SkiplaggedFetch, outcome, page, SkiplaggedSearchProvider

### Community 198 - "references/catalog.py"
Cohesion: 0.16
Nodes (8): fold(), LocationCatalog, MajorResolution, MajorSelection, test_catalog_major_messages_and_order(), test_fold_matches_assigned_python_unicode(), location_major_cases(), case()

### Community 199 - "json"
Cohesion: 0.09
Nodes (11): test_anywhere_case(), test_discovery_calls_case(), test_bad_json_is_value_error(), test_fixture_case(), test_plan_search_unchanged(), main(), rpc(), main() (+3 more)

### Community 200 - "DayColumn"
Cohesion: 0.20
Nodes (7): DateRibbon, .body, DayColumn, .background, .body, .date, .foreground

### Community 201 - "Implementation checklist and gates"
Cohesion: 0.29
Nodes (7): 1. Correct documentation and record the plan, 2. Connect existing Rust engine rules to Python, 3. Connect Fli and Skiplagged parsing, Deferred work, Design and boundaries, Implementation checklist and gates, P5.7 — Move the web backend onto the shared Rust core

### Community 202 - "P4.12 — Shared global resource pool"
Cohesion: 0.17
Nodes (12): 2. Implementation, 3. Configuration review, 4. Regression tests, 6. Risk analysis, 7. Recommended production configuration, 8. Owner decisions, Conservative live Fli ladder (owner-approved), Follow-up — priority tiers and low-priority headroom (2026-11-12) (+4 more)

### Community 204 - "OfferDetailView"
Cohesion: 0.09
Nodes (18): .accessibilityText, Array, OfferDetailView, .body, .steps, .summary, Step, airport (+10 more)

### Community 206 - "WorkStatus"
Cohesion: 0.42
Nodes (6): WorkStatus, _entry(), test_failed_terminal_requires_error_code(), test_failure_is_not_counted_as_covered(), test_succeeded_empty_cannot_carry_error_code(), test_unique_covered_combinations_does_not_double_count_providers()

### Community 207 - "SourceOffer"
Cohesion: 0.18
Nodes (8): FxNote, skiplagged_parse(), skiplagged::SourceOffer, skiplagged_tool_payload(), SkiplaggedError, Failed, SkiplaggedPage, SourceOffer

### Community 208 - "P5.5 — iPad feature parity"
Cohesion: 0.33
Nodes (6): Final review (fresh subagent, Opus), Next, P5.5 — iPad feature parity, Picker UX (owner decision during the device check), Rulings made during implementation, Verification

### Community 209 - "references/expansion.py"
Cohesion: 0.29
Nodes (4): expand_routes_and_dates(), RouteDateCombo, planning_case(), planning_cases()

### Community 210 - "P7.2 / P7.3: Discover contract and shared Rust selection"
Cohesion: 0.40
Nodes (5): Evidence (2026-11-21, worktree `CheapWings-p7`), Limitations, Owner decisions (Task 4 gate, 2026-11-21), P7.2 / P7.3: Discover contract and shared Rust selection, What exists now

### Community 211 - "MCPTransport"
Cohesion: 0.29
Nodes (3): MCPTransport, URLSessionMCPTransport, Task 2: Swift MCP client and Skiplagged provider

### Community 213 - "05 — Web + Native iOS Client Implementation"
Cohesion: 0.29
Nodes (7): 05 — Web + Native iOS Client Implementation, Polling and recovery design, Web first iOS second, Native SwiftUI implementation plan, Web and SwiftUI share remote search engine, P5 native iOS gate, Native SwiftUI P5

### Community 214 - "DiscoverySnapshot"
Cohesion: 0.16
Nodes (14): AnywherePage, core_query(), discovery_calls(), discovery::DiscoveryObservation, DiscoveryCall, DiscoveryObservation, DiscoveryPlanError, Rejected (+6 more)

### Community 216 - "Foundation"
Cohesion: 0.07
Nodes (11): CryptoKit, FliProbe, FliWreq, Foundation, PackageDescription, SelfTest, WreqProbe, FliProbeApp (+3 more)

### Community 217 - "fingerprint.rs"
Cohesion: 0.39
Nodes (5): fingerprint(), isoformat(), LocalInstant, Segment, isoformat_matches_python_shapes()

### Community 218 - "P5.2 — iPad app shell"
Cohesion: 0.29
Nodes (7): Behaviour and limits, Final review (fresh subagent, Opus), Next, Owner test on the fixed build — all-rows-rejected bug (2026-11-14), P5.2 — iPad app shell, Rulings made during implementation, Verification

### Community 222 - "ComboStatus"
Cohesion: 0.50
Nodes (4): ComboStatus, Done, Failed, Pending

### Community 225 - "FXSnapshot"
Cohesion: 0.40
Nodes (4): FXSnapshot, test_fx_snapshot_converts(), money_cases(), outcome()

### Community 226 - "P5.4 — Skiplagged on the iPad"
Cohesion: 0.33
Nodes (6): Final review (fresh subagent, Opus), Next, P5.4 — Skiplagged on the iPad, Rulings made during implementation, Verification, What exists now

### Community 227 - "Fli 0.25 s interval reliability (owner request, 2026-11-14)"
Cohesion: 0.67
Nodes (3): Fli 0.25 s interval reliability (owner request, 2026-11-14), Owner decision (2026-11-14), What 0.25 s means on each client

## Knowledge Gaps
- **267 isolated node(s):** `.session`, `.isGoogleStop`, `.hasLegs`, `.stopsText`, `page` (+262 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1402 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **64 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SearchSession` connect `SearchSession` to `Sendable`, `ResumeTests`, `ProviderPacing`, `SearchModel`, `DiscoveryOutcome`, `Repository`, `.start`, `.restoreLatest`, `P7 Discover — Readiness, Feasibility and Shared Rust Core Implementation Plan`, `DiscoverySessionTests`, `SearchStore`, `.body`, `StopReason`, `SearchPersistence`, `FakeClock`, `.testGoogleStopHoldsFliButSkiplaggedResumesNow`, `DaySummary`, `P5.2 — iPad app shell`, `EmptyOutcome`?**
  _High betweenness centrality (0.156) - this node is a cross-community bridge._
- **Are the 48 inferred relationships involving `ProviderFailure` (e.g. with `JobRunner` and `ExactCapture`) actually correct?**
  _`ProviderFailure` has 48 INFERRED edges - model-reasoned connections that need verification._
- **What connects `.session`, `.isGoogleStop`, `.hasLegs` to the rest of the system?**
  _267 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_scheduler.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09444444444444444 - nodes in this community are weakly interconnected._
- **Why does `P4.12 — Shared global resource pool` connect `P4.12 — Shared global resource pool` to `WORK_LOG.md — Current State (keep under ~80 lines)`, `Repository`, `types.ts`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **Are the 88 inferred relationships involving `Repository` (e.g. with `AirportTransfer` and `IdentityConfidence`) actually correct?**
  _`Repository` has 88 INFERRED edges - model-reasoned connections that need verification._
- **Should `Sendable` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._