# Graph Report - p5.05-native-ios-analysis  (2026-11-14)

## Corpus Check
- 282 files · ~436,254 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 29 file(s) not represented in the graph (top: (none) 16, .jsonl 5, .css 3)

## Summary
- 3038 nodes · 7856 edges · 189 communities (123 shown, 66 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 1467 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `89c7ecc8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- .create_job
- .run
- Money
- OctotripProvider
- test_p49_review.py
- fake.py
- base
- sqlalchemy
- P46ResultsWorkspace.tsx
- rust/src/lib.rs
- test_fli.py
- create_app
- App.tsx
- StatusVisuals.tsx
- 04 — Data, Persistence, and REST API Contracts
- XCTestCase
- CheapWings
- base
- test_api.py
- WORK_LOG.md — Current State (keep under ~80 lines)
- Provider and result-cache research (2026-11-10)
- Experiment
- SearchSession
- types.ts
- SearchForm.tsx
- Itinerary
- pytest
- common
- package.json
- compilerOptions
- p5.05.md
- test_search_cache.py
- p412-browser.mjs
- compilerOptions
- P4.10 — Smart location selection
- P5.05 — Native iOS search engine feasibility analysis
- 03 — Provider Feasibility, Multi-Provider Aggregation, and Fare Accuracy
- Repository
- P4.12 — Shared global resource pool
- swoop.py
- P4.11 — Fli as a fourth provider
- contracts.py
- routes.py
- json
- AirportSelection
- expand_routes_and_dates
- 01 — Product Requirements, Rules, and UX Acceptance
- p46-browser.mjs
- fli.rs
- ThrowingStore
- cheapwings-ffi/src/lib.rs
- scripts
- MIT airport data license
- .oxlintrc.json
- browser.mjs
- fake.py
- p48_throughput.py
- Reusable SVG icon sprite
- vite-env.d.ts
- tsconfig.json
- locations.rs
- index.html
- Web favicon: purple lightning bolt
- React atom logo SVG
- Web HTML entry
- cheapwings
- CheapWings P4.8 — Throughput, Concurrency & Reliability Experiment
- provider-feasibility-evidence.md
- ResumeTests
- FakeTransport
- ProviderFailure
- P4.5 UI/UX handover, intake and fixes
- provider_failure
- 19. Python Tech Stack Decision, Long-Running Jobs, and Cross-Platform Integration
- P4.8 — Provider interval benchmark and scheduling plan (2026-11-10)
- FlightFinder — Architecture & Design Review Handoff
- 17. Mandatory Multi-Provider Aggregation Architecture (restored; mandatory)
- 12. MVP Milestones and Checkpoints
- test_locations.py
- provider_probe_swoop.py
- 18. Web + Native iOS Product Design
- 1. Product Intent, Requirements, and Non-Goals
- 2. Proposed Search Experience / UX
- 3. Candidate Data Sources and Due-Diligence Notes
- 15. Mandatory Deliverables from the Reviewing Agent
- 5. Search Algorithm, Coverage, and Failure Handling
- 6. Fare Data Model & Comparability
- provider_probe_skiplagged.py
- 11. Minimal Test Plan and Evaluation Matrix
- 20. Mandatory Cross-Platform and Multi-Provider Acceptance Tests
- 4. Architecture Proposal
- 7. Price Verification Policy
- 8. Filtering and Travel Risks
- AGENTS.md
- CLAUDE.md
- fixtures.rs
- Decimal
- shadow_money.py
- test_locations.py
- search
- build_location_catalog.py
- Tfs
- ItineraryInfo
- pytest
- verification.py
- Fli probe — P5.06 spikes S1 (iPhone) and S3 (Swift off-device)
- PackageDescription
- money.rs
- SwiftCore
- build.sh
- fli-wreq
- cheapwings-money-rs
- cheapwings-money-rs
- LocationCatalog
- test_overlap_429_retry_after_and_independent_provider
- P5.3 — iPad persistence and resume
- drain
- ranking.rs
- gen_core_fixtures.py
- SwoopProvider
- test_core_fixtures.py
- fli-wreq/src/lib.rs
- build-ios.sh
- rust/build.sh
- SearchEvent
- core-s5
- SearchModel
- fingerprint.rs
- cheapwings-core
- cheapwings-ffi
- cheapwings-py
- Sendable
- Foundation
- cheapwings-store/src/lib.rs
- repository.py
- StopReason
- Outcome
- CoreError
- UserAgentMode
- gen_fixtures.py
- 06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria
- S5Section
- p45-browser.mjs
- MaxStops
- dependencies
- datetime
- cheapwings-core

## God Nodes (most connected - your core abstractions)
1. `Repository` - 113 edges
2. `ProviderFailure` - 100 edges
3. `FakeProvider` - 94 edges
4. `Registration` - 94 edges
5. `JobRunner` - 66 edges
6. `SearchSession` - 54 edges
7. `SearchQuery` - 50 edges
8. `Offer` - 42 edges
9. `now_ms()` - 42 edges
10. `Money` - 40 edges

## Surprising Connections (you probably didn't know these)
- `Rulings made during implementation` --references--> `SearchPersistence`  [INFERRED]
  docs/log/p5.3.md → apps/ios/CheapWingsKit/Sources/CheapWingsKit/Persistence.swift
- `Rulings made during implementation` --references--> `FoundOffer`  [INFERRED]
  docs/log/p5.2.md → apps/ios/CheapWingsKit/Sources/CheapWingsKit/SearchEngine.swift
- `3. Native engine design and module ownership` --references--> `Money`  [INFERRED]
  docs/log/p5.05.md → backend/src/cheapwings/domain/money.py
- `Verification` --references--> `SearchSession`  [INFERRED]
  docs/log/p5.2.md → apps/ios/CheapWingsKit/Sources/CheapWingsKit/SearchSession.swift
- `17.2 Separate itinerary from offer` --references--> `Itinerary`  [INFERRED]
  docs/reference/V4_FULL_DESIGN_REFERENCE.md → backend/src/cheapwings/domain/itinerary.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Planned SwiftUI shares backend contract and durable recovery** — docs_05_web_and_native_ios_swiftui_plan, docs_06_implementation_checkpoints_p5, readme_ios_planned [EXTRACTED 1.00]
- **Exact identity, exact money and unknown-safe rankings** — docs_03_providers_aggregation_pricing_itinerary_offer_identity, docs_03_providers_aggregation_pricing_decimal_money_fx, docs_01_product_requirements_ux_safe_and_advertised_rankings, docs_04_data_and_api_contracts_three_valued_unknowns [INFERRED 0.85]
- **Canonical fare evidence remains conservative across adapters and clients** — docs_03_providers_aggregation_pricing_money, docs_04_data_and_api_contracts_three_valued, docs_log_p4_11_fare_limits, readme_safe_ranking [INFERRED 0.95]

## Communities (189 total, 66 thin omitted)

### Community 0 - ".create_job"
Cohesion: 0.11
Nodes (40): DispatchFailure, JobRunner, Registration, test_fli_real_normalization_api_prices_and_cache(), transport(), test_fli_uses_durable_shared_fetch_cancel_fencing_and_cache(), test_missing_fli_payload_is_failure_and_never_cached(), test_short_source_expiry_preserves_other_source_and_running_job() (+32 more)

### Community 1 - ".run"
Cohesion: 0.13
Nodes (9): Decoded, DecodeError, .description, partialPayload, schemaChanged, Leg, Offer, Page (+1 more)

### Community 2 - "Money"
Cohesion: 0.12
Nodes (10): _core_call(), Money, UnknownCurrencyError, test_cannot_compare_different_currencies(), test_fx_snapshot_converts(), test_idr_has_zero_minor_units(), test_money_rejects_float(), test_money_requires_known_currency_for_minor_units() (+2 more)

### Community 3 - "OctotripProvider"
Cohesion: 0.11
Nodes (15): OctotripProvider, HttpStartGate, test_octotrip_429_stops_unsent_peer_http(), test_octotrip_gate_covers_initialization_across_three_sessions(), respond(), payload(), query(), test_bad_source_values_fail_or_disable_navigation() (+7 more)

### Community 4 - "test_p49_review.py"
Cohesion: 0.08
Nodes (26): BoundedCall, __init__(), test_bounded_swoop_executor_c3_has_actual_overlap_and_no_queue(), __init__(), __init__(), __init__(), Synth, MeasuredProduction (+18 more)

### Community 5 - "fake.py"
Cohesion: 0.15
Nodes (22): PublicOffer, public_offer(), shortlist(), ComparisonStatus, LinkScope, PriceStatus, ThreeValued, ItineraryGroup (+14 more)

### Community 6 - "base"
Cohesion: 0.06
Nodes (34): CODE_SIGN_STYLE, CURRENT_PROJECT_VERSION, GENERATE_INFOPLIST_FILE, INFOPLIST_KEY_UILaunchScreen_Generation, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPad, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPhone, MARKETING_VERSION, PRODUCT_BUNDLE_IDENTIFIER (+26 more)

### Community 7 - "sqlalchemy"
Cohesion: 0.10
Nodes (8): upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), query()

### Community 8 - "P46ResultsWorkspace.tsx"
Cohesion: 0.13
Nodes (29): PriceStatus, PublicItinerary, PublicOffer, FareRiskNotice(), formatDuration(), ItineraryCard(), BAG_LABEL, COMPARISON_LABEL (+21 more)

### Community 9 - "rust/src/lib.rs"
Cohesion: 0.18
Nodes (22): as_minor_units(), best_checked_deal(), exponent(), EXPONENTS, fingerprint(), FingerprintCase, Fixtures, from_minor_units() (+14 more)

### Community 10 - "test_fli.py"
Cohesion: 0.19
Nodes (14): decoder(), payload(), provider(), query(), test_c3_real_threads_overlap_and_cancel_retains_physical_capacity(), fetch(), test_challenge_redirect_is_not_followed(), test_exact_prices_identity_and_conservative_evidence() (+6 more)

### Community 11 - "create_app"
Cohesion: 0.19
Nodes (10): create_app(), cancel(), create_search(), get_job(), get_results(), health(), lifespan(), _exact_reprice_count() (+2 more)

### Community 12 - "App.tsx"
Cohesion: 0.13
Nodes (23): api, ApiError, BASE_URL, request(), TERMINAL_STATUSES, errorMessage(), getOwnerToken(), setOwnerToken() (+15 more)

### Community 13 - "StatusVisuals.tsx"
Cohesion: 0.27
Nodes (10): ProviderProgress, WorkerPool, LABEL, P46SearchProgress(), PoolGauge(), ProviderBars(), SEGMENTS, SOURCE_NAMES (+2 more)

### Community 14 - "04 — Data, Persistence, and REST API Contracts"
Cohesion: 0.12
Nodes (16): Scheduler design requirements, Authentication and secret boundary, Canonical Money Itinerary Offer Coverage, Coverage and terminal statuses, 04 — Data, Persistence, and REST API Contracts, Normative versioned REST design, Normative versioned REST v1 and canonical DTOs, SQLite persistence schema direction (+8 more)

### Community 15 - "XCTestCase"
Cohesion: 0.09
Nodes (12): AppDelegate, ContinuedSearch, StoreTests, SearchStore, Global Constraints, Out of scope, P5.3 iPad Persistence and Resume Implementation Plan, Review Focus (+4 more)

### Community 16 - "CheapWings"
Cohesion: 0.08
Nodes (33): Synthetic browser regressions, CheapWings web, React TypeScript Vite thin client, Runtime private access, Memory-only web owner token, Intercepted Playwright browser regression suite, React Vite thin client, Bounded blocking provider execution (+25 more)

### Community 17 - "base"
Cohesion: 0.05
Nodes (37): CODE_SIGN_STYLE, CURRENT_PROJECT_VERSION, GENERATE_INFOPLIST_FILE, INFOPLIST_KEY_CFBundleDisplayName, INFOPLIST_KEY_UILaunchScreen_Generation, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPad, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPhone, MARKETING_VERSION (+29 more)

### Community 18 - "test_api.py"
Cohesion: 0.19
Nodes (19): client_for(), request_data(), test_auth_and_remote_boundary(), test_baggage_eligibility_and_snapshot_cursor(), test_capabilities_report_default_source_selection(), test_invalid_input_no_job(), test_openapi_committed_and_response_shapes(), test_quota_and_cancel() (+11 more)

### Community 19 - "WORK_LOG.md — Current State (keep under ~80 lines)"
Cohesion: 0.10
Nodes (24): Canonical evidence-preserving extensions, Pre-restructure WORK_LOG header (baseline, full tracker, ledger, summary, deviations), 2026-11-09 empty-repo baseline, Historical initial repository and toolchain, Pre-restructure phase summary, FlightFinder renamed CheapWings, Owner acceptance and merge4c98386, Evidence and phase-history index (+16 more)

### Community 20 - "Provider and result-cache research (2026-11-10)"
Cohesion: 0.06
Nodes (32): request_snapshot(), Cache and OctoTrip implementation kickoff (2026-11-10), Current code audit — implications for caching, Dated provider evaluation — primary sources, not production approval, Final live acceptance and handover — cache + OctoTrip, Hosted endpoint preflight — actual observations and limits, Implementation checkpoint — durable cache and backend selection (in progress), Live owner search — cross-provider overlap confirmed (2026-11-10) (+24 more)

### Community 21 - "Experiment"
Cohesion: 0.12
Nodes (8): Experiment, post(), wrap(), observed(), test_octotrip_three_sessions_share_one_http_gate(), session(), test_response_timing_preserves_stream_bytes(), respond()

### Community 22 - "SearchSession"
Cohesion: 0.11
Nodes (13): Phase, idle, running, stopped, ResumeInfo, SearchSession, .canResume, .doneSoFar (+5 more)

### Community 23 - "types.ts"
Cohesion: 0.10
Nodes (17): AirportTransfer, ComparisonStatus, Coverage, ExpiredObservation, IdentityConfidence, Job, JobPhase, JobStatus (+9 more)

### Community 24 - "SearchForm.tsx"
Cohesion: 0.17
Nodes (17): Currency, ProviderCapability, SearchRequest, AirportMultiSelect(), Props, Props, SearchForm(), todayIso() (+9 more)

### Community 25 - "Itinerary"
Cohesion: 0.09
Nodes (24): airport_transfers(), AirportTransfer, compute_fingerprint(), IdentityConfidence, Itinerary, FlightSegment, build_itinerary(), MatchEngine (+16 more)

### Community 27 - "common"
Cohesion: 0.06
Nodes (38): PRODUCT_BUNDLE_IDENTIFIER, platform, settings, sources, type, CODE_SIGNING_ALLOWED, GENERATE_INFOPLIST_FILE, INFOPLIST_KEY_UILaunchScreen_Generation (+30 more)

### Community 28 - "package.json"
Cohesion: 0.13
Nodes (19): devDependencies, oxlint@^1.90.0, @types/node@^24.19.2, @types/react@^19.3.0, @types/react-dom@^19.3.0, typescript@~7.0.2, vite@^8.3.6, @vitejs/plugin-react@^6.1.2 (+11 more)

### Community 29 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 30 - "p5.05.md"
Cohesion: 0.18
Nodes (8): Decision status, Owner decision (2026-11-13, after S5), P5.06 — Native engine spikes (S1–S5), Reproduce, Results, Global Constraints, Out of scope (later phases), P5.1 Shared Rust Core Implementation Plan

### Community 31 - "test_search_cache.py"
Cohesion: 0.22
Nodes (21): ProviderResultCache, Counted, finish(), setup(), test_absolute_retention_deadline_expires_inherited_job_and_purges(), test_additive_migration_preserves_populated_work_attempt_and_quote_history(), test_cache_eviction_bytes_policy_revocation_and_filter_reapplication(), test_cache_reuse_is_independent_of_other_selected_sources() (+13 more)

### Community 32 - "p412-browser.mjs"
Cohesion: 0.17
Nodes (9): playwright@^1.65.0, dist, evidence, shots, dist, dist, job, pool (+1 more)

### Community 33 - "compilerOptions"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 34 - "P4.10 — Smart location selection"
Cohesion: 0.16
Nodes (17): Exhaustive combination coverage, P4.10 historical offline acceptance, Backend authoritative Major resolution, Typed Major backend authority, Legacy IATA caller compatibility, P4.10 — Smart location selection, Catalog limitations, P4.10 staged localhost and authorized live wiring (+9 more)

### Community 35 - "P5.05 — Native iOS search engine feasibility analysis"
Cohesion: 0.15
Nodes (12): ResultsExpired, 10. Sources, facts and open questions, 1. Executive verdict, 2. Provider compatibility matrix, 3. Native engine design and module ownership, 4. Port-vs-drop matrix, 5. Background / foreground behaviour (iOS), 6. Risk register (likelihood × impact, 1–5) (+4 more)

### Community 36 - "03 — Provider Feasibility, Multi-Provider Aggregation, and Fare Accuracy"
Cohesion: 0.12
Nodes (17): Exact decimal money and FX provenance, 03 — Provider Feasibility, Multi-Provider Aggregation, and Fare Accuracy, Normalized provider error taxonomy, Itinerary versus seller offer, Conservative itinerary identity and separate fare offers, Comparable exact money, Typed provider failures versus successful empty, P0 provider feasibility gate (+9 more)

### Community 37 - "Repository"
Cohesion: 0.13
Nodes (33): FakeProvider, write_session(), now_ms(), Repository, fetch(), test_actual_start_deadline_and_cooldown_survive_restart(), test_cancel_before_adapter_entry_makes_no_upstream_call(), test_continuous_new_jobs_do_not_starve_already_served_jobs() (+25 more)

### Community 38 - "P4.12 — Shared global resource pool"
Cohesion: 0.17
Nodes (12): 2. Implementation, 3. Configuration review, 4. Regression tests, 6. Risk analysis, 7. Recommended production configuration, 8. Owner decisions, Conservative live Fli ladder (owner-approved), Follow-up — priority tiers and low-priority headroom (2026-11-12) (+4 more)

### Community 39 - "swoop.py"
Cohesion: 0.11
Nodes (18): SourceEvidence, ItinerarySummary, FXSnapshot, ProviderCapabilities, aware_iso(), decimal_value(), json_payload(), money() (+10 more)

### Community 40 - "P4.11 — Fli as a fourth provider"
Cohesion: 0.11
Nodes (19): Historical usable quote verification, P4.11 — Fli as a fourth provider, Truthful failure and cache semantics, Fourth provider Fli public Google Flights page, P4.11 acceptance evidence, Explicit HTTP2 transport, Indicative Google quotes and generic search links, Historical HTTP2 live measurements (+11 more)

### Community 41 - "contracts.py"
Cohesion: 0.16
Nodes (18): capabilities(), worker_pool(), AirportTransfer, Capabilities, Coverage, Created, DTO, ExpiredObservation (+10 more)

### Community 42 - "routes.py"
Cohesion: 0.10
Nodes (15): Settings, default_registry(), database(), require_current_schema(), CapacityExceeded, main(), worker_lock(), test_fourth_registration_configuration_and_no_false_capabilities() (+7 more)

### Community 43 - "json"
Cohesion: 0.09
Nodes (14): live_guard(), main(), trial(), main(), Measurements, ObservedProvider, observers(), make_send() (+6 more)

### Community 44 - "AirportSelection"
Cohesion: 0.09
Nodes (20): AirportPicker, .body, AirportToggleRow, .body, ChipLabelStyle, PlaceAirports, .body, PlaceLink (+12 more)

### Community 45 - "expand_routes_and_dates"
Cohesion: 0.35
Nodes (7): expand_routes_and_dates(), RouteDateCombo, _query(), test_1x3x9_expands_to_27_combinations(), test_combos_are_unique_and_deterministic_order(), test_duplicate_input_codes_are_deduplicated_before_expansion(), test_same_origin_destination_pair_is_skipped()

### Community 46 - "01 — Product Requirements, Rules, and UX Acceptance"
Cohesion: 0.22
Nodes (10): Accessible responsive UI, 01 — Product Requirements, Rules, and UX Acceptance, One-way adult economy flight finder, Flexible one-way finder scope, Query coverage differs from inventory completeness, Conservative fare ranking, Safe Best checked and Lowest advertised views, Honest results states (+2 more)

### Community 47 - "p46-browser.mjs"
Cohesion: 0.28
Nodes (6): all, dist, job, offer(), richEntries, trip()

### Community 48 - "fli.rs"
Cohesion: 0.09
Nodes (36): airport_changes(), CheckedOffers, cross_check(), currency_from_token(), decode_page(), extract_ds1(), filter_offers(), FliError (+28 more)

### Community 50 - "cheapwings-ffi/src/lib.rs"
Cohesion: 0.06
Nodes (40): fingerprint_matches_python(), ranking_matches_python(), AirportChange, best_checked_deal(), combo_from_store(), ComboStatus, Done, Failed (+32 more)

### Community 51 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:browser

### Community 52 - "MIT airport data license"
Cohesion: 0.33
Nodes (5): Airportsdata and mwgg Airports MIT attribution, MIT airport data license, Airportsdata and mwgg Airports MIT attribution, MIT airport data license, P4.10 offline typed location catalog

### Community 53 - ".oxlintrc.json"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 54 - "browser.mjs"
Cohesion: 0.33
Nodes (3): capabilities, dist, job

### Community 55 - "fake.py"
Cohesion: 0.12
Nodes (20): main(), run_demo(), CoverageEntry, unique_covered_combinations(), WorkStatus, minor_unit_exponent(), ProviderErrorCode, ScriptedOutcome (+12 more)

### Community 56 - "p48_throughput.py"
Cohesion: 0.09
Nodes (18): quantile(), live_guard(), batch(), emit(), main(), provider_run(), migrated(), peak() (+10 more)

### Community 57 - "Reusable SVG icon sprite"
Cohesion: 0.67
Nodes (3): Bluesky, Discord, GitHub and X logos, Reusable SVG icon sprite, Purple documentation and social profile icons

### Community 60 - "locations.rs"
Cohesion: 0.11
Nodes (14): Catalog, CatalogError, Invalid, NoMajorMapping, StaleVersion, TooLong, TypeMismatch, UnknownLocation (+6 more)

### Community 75 - "CheapWings P4.8 — Throughput, Concurrency & Reliability Experiment"
Cohesion: 0.12
Nodes (16): Alternative architecture assessment, Authorization and method, CheapWings P4.8 — Throughput, Concurrency & Reliability Experiment, Experiment A — completed live results, Experiment B — offline Python scheduler stress, Experiment C — offline overlapping failure injection, Follow-up — requested C3/1s trials and swoop retry (2026-11-11 Jakarta), Follow-up sanitized per-search ledger (+8 more)

### Community 76 - "provider-feasibility-evidence.md"
Cohesion: 0.13
Nodes (15): Claims vs observed, Claims vs observed, Combined P0 gate outcome, Fields present / absent (for canonical domain mapping), Follow-up probe items, Legal/compliance note (the real risk for swoop), Live sample (redacted selector/links kept short; full in fixture), Owner decisions (resolved 2026-11-09, per `docs/06` stop/escalation rule) (+7 more)

### Community 77 - "ResumeTests"
Cohesion: 0.18
Nodes (3): FoundOffer, ResumeTests, Task 2: Session checkpointing and resume (CheapWingsKit)

### Community 78 - "FakeTransport"
Cohesion: 0.17
Nodes (6): FakeClock, .sleep, .sleeps, FakeTransport, page(), SearchEngineTests

### Community 79 - "ProviderFailure"
Cohesion: 0.07
Nodes (23): ProviderFailure, exact_http_client(), observe(), ExactCapture, FliProvider, provider_failure(), retry_after(), mcp_search() (+15 more)

### Community 80 - "P4.5 UI/UX handover, intake and fixes"
Cohesion: 0.14
Nodes (17): P2–P4 implementation log, Historical CGK to CTS cancelled review, P2 recorded acceptance, P3 adapter normalization and acceptance, P4 React implementation, P4 typed client and polling reliability, Polling effects and stale-page fencing, Historical review follow-ups (+9 more)

### Community 81 - "provider_failure"
Cohesion: 0.18
Nodes (11): Checkpoints 4–5 — implementation and offline verification, Confirmed runtime cause and correction — 2026-11-11, Latest local live search outcome — 2026-11-11, Local live-site wiring — 2026-11-11, Merge status correction — 2026-11-11, Owner merge handoff — 2026-11-11, Owner testing and publication authorization — 2026-11-11, P4.9 Checkpoints 1–3 — 2026-11-11, Option A approved (+3 more)

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

### Community 87 - "test_locations.py"
Cohesion: 0.11
Nodes (12): fold(), LocationCatalog, MajorResolution, MajorSelection, Global Constraints, Out of scope, P5.5 iPad Feature Parity Implementation Plan, Review Focus (+4 more)

### Community 88 - "provider_probe_swoop.py"
Cohesion: 0.29
Nodes (5): summarize(), cell(), fmt(), load(), main()

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

### Community 96 - "provider_probe_skiplagged.py"
Cohesion: 0.12
Nodes (8): main(), main(), run(), _utc_now_iso(), main(), run(), _to_jsonable(), _utc_now_iso()

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
Cohesion: 0.06
Nodes (29): airport_lookup_has_timezone(), catalog(), CATALOG, FingerprintCase, Fixtures, fixtures(), FIXTURES, fli_pages_match_python() (+21 more)

### Community 106 - "Decimal"
Cohesion: 0.14
Nodes (14): as_minor_units(), cheapwings_core(), from_minor_units(), fx_convert(), minor_unit_exponent(), to_py(), as_minor_units(), cheapwings_money_rs() (+6 more)

### Community 107 - "shadow_money.py"
Cohesion: 0.16
Nodes (9): check(), py_convert(), same(), pytest_configure(), as_minor_units(), convert(), from_minor_units(), minor_unit_exponent() (+1 more)

### Community 108 - "test_locations.py"
Cohesion: 0.29
Nodes (9): resolve_location(), catalog(), selection(), test_ambiguous_cities_keep_distinct_ids_and_geography(), test_catalog_rejects_inconsistent_data(), test_lookup(), test_major_resolution_and_no_fallback(), test_parent_browse_never_resolves_to_search_automatically() (+1 more)

### Community 112 - "ItineraryInfo"
Cohesion: 0.09
Nodes (15): OfferDetailView, .body, .header, OfferRow, .summary, ResultsView, .body, .session (+7 more)

### Community 113 - "pytest"
Cohesion: 0.23
Nodes (13): SearchQuery, plan_scope(), test_boundary_and_overlap_match_expansion(), test_zero_routes_and_date_changes(), _base(), test_include_hidden_city_defaults_false_and_does_not_silently_flip(), test_rejects_excessive_combination_count(), test_rejects_invalid_iata() (+5 more)

### Community 114 - "verification.py"
Cohesion: 0.17
Nodes (10): Offer, ProviderRepriceResult, ProviderSearchResult, RepriceRequest, SearchProvider, SingleDateRouteQuery, offer_from_row(), VerificationRepository (+2 more)

### Community 115 - "Fli probe — P5.06 spikes S1 (iPhone) and S3 (Swift off-device)"
Cohesion: 0.33
Nodes (5): Fli probe — P5.06 spikes S1 (iPhone) and S3 (Swift off-device), Offline check (no network), S1 — physical iPhone (needs full Xcode, owner-approved live requests), S3 — Swift off-device (macOS pre-check), What this does not do

### Community 117 - "money.rs"
Cohesion: 0.23
Nodes (11): as_minor_units(), EXPONENTS, from_minor_units(), fx_convert(), minor_unit_exponent(), MoneyError, InvalidDecimal, NotWholeMinorUnits (+3 more)

### Community 119 - "SwiftCore"
Cohesion: 0.06
Nodes (41): FingerprintCase, Fixtures, FixtureTests, InstantJ, LegJ, MoneyCase, OfferExpectJ, OfferJ (+33 more)

### Community 120 - "build.sh"
Cohesion: 0.33
Nodes (5): DEVELOPER_DIR, IPHONEOS_DEPLOYMENT_TARGET, MACOSX_DEPLOYMENT_TARGET, PATH, build.sh script

### Community 128 - "LocationCatalog"
Cohesion: 0.17
Nodes (5): CatalogError, Failed, Location, LocationCatalog, MajorResolution

### Community 129 - "test_overlap_429_retry_after_and_independent_provider"
Cohesion: 0.18
Nodes (16): claim(), engine(), migrate(), reg(), drain(), record(), short(), recover() (+8 more)

### Community 130 - "P5.3 — iPad persistence and resume"
Cohesion: 0.14
Nodes (11): Final review (fresh subagent, Opus), Next, Owner-found crash and the continued-processing decision, P5.3 — iPad persistence and resume, Rulings made during implementation, Verification, Next, P5.5 — iPad feature parity (+3 more)

### Community 131 - "drain"
Cohesion: 0.15
Nodes (14): test_api_scheduler_results_contract(), test_pagination_freezes_incremental_quote_set(), payload(), test_airport_change_never_claims_ground_cost_is_known_on_reprice(), reprice(), search(), test_skiplagged_names_stay_summary_metadata_without_invented_flights(), test_surface_change_and_carriers_survive_worker_storage_api() (+6 more)

### Community 132 - "ranking.rs"
Cohesion: 0.42
Nodes (5): best_checked_deal(), lowest_advertised(), priced(), RankOffer, tier()

### Community 133 - "gen_core_fixtures.py"
Cohesion: 0.13
Nodes (23): currency_token(), expected_offer(), fingerprint_cases(), fli_leg(), fli_page_cases(), fli_row(), fli_tfs_cases(), instant() (+15 more)

### Community 134 - "SwoopProvider"
Cohesion: 0.23
Nodes (11): SwoopProvider, load(), query(), test_dst_ambiguity_rejected(), test_missing_zone_retains_unmatched_summary(), test_skiplagged_exact_money_unknown_fields_and_no_fake_segments(), test_swoop_p0_timezone_identity_and_unknown_risk(), test_swoop_seller_basic_mismatch_and_estimate_never_exact() (+3 more)

### Community 135 - "test_core_fixtures.py"
Cohesion: 0.15
Nodes (14): test_generator_money_reference_runs_without_rust_core(), _python_api_result(), test_beyond_28_digits_is_exact(), test_beyond_96_bit_raises_instead_of_rounding(), test_core_module_is_rust(), test_missing_core_module_names_the_fix(), test_money_fixtures_through_python_api(), test_unknown_currency_raises_unknown_currency_error() (+6 more)

### Community 136 - "fli-wreq/src/lib.rs"
Cohesion: 0.24
Nodes (7): MAX_BODY, wreq_fetch(), WreqError, Build, Request, TooLarge, WreqResponse

### Community 137 - "build-ios.sh"
Cohesion: 0.33
Nodes (5): DEVELOPER_DIR, IPHONEOS_DEPLOYMENT_TARGET, MACOSX_DEPLOYMENT_TARGET, PATH, build-ios.sh script

### Community 138 - "rust/build.sh"
Cohesion: 0.33
Nodes (5): DEVELOPER_DIR, IPHONEOS_DEPLOYMENT_TARGET, MACOSX_DEPLOYMENT_TARGET, PATH, build.sh script

### Community 139 - "SearchEvent"
Cohesion: 0.13
Nodes (10): .stored, SearchEvent, comboFailed, offers, offersHidden, progress, started, stopped (+2 more)

### Community 142 - "SearchModel"
Cohesion: 0.07
Nodes (11): .body, SearchModel, .canSearch, .plan, .planSummary, SearchView, .body, Side (+3 more)

### Community 145 - "fingerprint.rs"
Cohesion: 0.39
Nodes (4): fingerprint(), isoformat(), LocalInstant, Segment

### Community 150 - "Sendable"
Cohesion: 0.06
Nodes (30): .body, FetchedPage, FliTransport, isAllowedFliRedirect(), RedirectPolicy, .refused, TransportError, notHTTP (+22 more)

### Community 151 - "Foundation"
Cohesion: 0.06
Nodes (21): CheapWingsApp, Array, Tfs, twoLegPage(), BackgroundTasks, CheapWingsCore, CheapWingsKit, Foundation (+13 more)

### Community 152 - "cheapwings-store/src/lib.rs"
Cohesion: 0.05
Nodes (44): civil_from_days(), days_from_civil(), format_date(), normalize(), parse_date(), plan_search(), PlanError, DatesReversed (+36 more)

### Community 153 - "repository.py"
Cohesion: 0.10
Nodes (23): results_projection(), cache_key(), CacheRepository, without_handles(), Base, FareQuote, FXRow, ItineraryRow (+15 more)

### Community 156 - "StopReason"
Cohesion: 0.08
Nodes (12): Date, .milliseconds, SearchPersistence, .isProviderStop, .storedText, StopReason, backgrounded, blocked (+4 more)

### Community 157 - "Outcome"
Cohesion: 0.15
Nodes (16): FliProbe, isAllowedRedirect(), Outcome, blockedRedirect, blockedSorry, blockedTraffic, crossCheckFailed, httpError (+8 more)

### Community 158 - "CoreError"
Cohesion: 0.21
Nodes (10): fx_negative_zero_keeps_sign(), money_matches_python(), money_result(), MoneyCase, as_minor_units(), CoreError, Invalid, from_minor_units() (+2 more)

### Community 159 - "UserAgentMode"
Cohesion: 0.20
Nodes (9): UserAgentMode, chromeDesktop, .header, safariIOS, safariIPad, system, Transport, urlSession (+1 more)

### Community 161 - "gen_fixtures.py"
Cohesion: 0.19
Nodes (6): fingerprint_cases(), instant(), money_cases(), offer(), outcome(), ranking_cases()

### Community 162 - "06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria"
Cohesion: 0.08
Nodes (25): Provider feasibility and permission gate, 05 — Web + Native iOS Client Implementation, Polling and recovery design, Web first iOS second, Native SwiftUI implementation plan, Web and SwiftUI share remote search engine, 06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria, Fundamental incompatibility escalation (+17 more)

### Community 164 - "S5Section"
Cohesion: 0.12
Nodes (9): FliProbe, FliWreq, WreqProbe, FliProbeApp, .body, ProbeView, .body, S5Section (+1 more)

### Community 166 - "p45-browser.mjs"
Cohesion: 0.33
Nodes (5): baseJob, commonOffer, dist, itinerary, query

### Community 170 - "dependencies"
Cohesion: 0.50
Nodes (4): dependencies, react@^19.3.1, react-dom@^19.3.1, react-dom

### Community 173 - "datetime"
Cohesion: 0.11
Nodes (6): DispatchDeferred, zones(), peak(), query(), scenario(), threads()

## Knowledge Gaps
- **202 isolated node(s):** `.majorCodes`, `.body`, `.session`, `.planSummary`, `.canSearch` (+197 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1039 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **66 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Review Focus` connect `SwiftCore` to `Money`, `p5.05.md`, `test_core_fixtures.py`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._
- **Are the 88 inferred relationships involving `Repository` (e.g. with `AirportTransfer` and `IdentityConfidence`) actually correct?**
  _`Repository` has 88 INFERRED edges - model-reasoned connections that need verification._
- **What connects `.majorCodes`, `.body`, `.session` to the rest of the system?**
  _202 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `.create_job` be split into smaller, more focused modules?**
  _Cohesion score 0.10862470862470862 - nodes in this community are weakly interconnected._
- **Why does `Task 1: Workspace, shared fixtures and Rust money` connect `SwiftCore` to `CoreError`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Are the 42 inferred relationships involving `ProviderFailure` (e.g. with `JobRunner` and `ExactCapture`) actually correct?**
  _`ProviderFailure` has 42 INFERRED edges - model-reasoned connections that need verification._
- **Should `.run` be split into smaller, more focused modules?**
  _Cohesion score 0.12873563218390804 - nodes in this community are weakly interconnected._