# Graph Report - p5.05-native-ios-analysis  (2026-11-13)

## Corpus Check
- 209 files · ~306,716 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 21 file(s) not represented in the graph (top: (none) 8, .jsonl 5, .css 3)

## Summary
- 1931 nodes · 5484 edges · 127 communities (96 shown, 31 thin omitted)
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 1214 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b14de0e3`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Repository
- .run
- Money
- test_octotrip.py
- test_p49_review.py
- swoop.py
- base
- sqlalchemy
- P46ResultsWorkspace.tsx
- money-pyo3/src/lib.rs
- test_fli.py
- routes.py
- App.tsx
- StatusVisuals.tsx
- 06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria
- minor_unit_exponent
- CheapWings
- catalog.py
- test_api.py
- WORK_LOG.md — Current State (keep under ~80 lines)
- Provider and result-cache research (2026-11-10)
- Experiment
- SwoopProvider
- types.ts
- SearchForm.tsx
- Itinerary
- pytest
- .search
- package.json
- compilerOptions
- P5.05 — Native iOS search engine feasibility analysis
- repository.py
- p412-browser.mjs
- compilerOptions
- P4.10 — Smart location selection
- 06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria
- 03 — Provider Feasibility, Multi-Provider Aggregation, and Fare Accuracy
- 08 — Starting Prompt for a Local Coding Agent
- BoundedCall
- fli-wreq/src/lib.rs
- P4.11 — Fli as a fourth provider
- contracts.py
- p48_intervals.py
- pathlib
- ProbeResult
- expand_routes_and_dates
- 01 — Product Requirements, Rules, and UX Acceptance
- p46-browser.mjs
- Outcome
- test_swoop_rpc.py
- p45-browser.mjs
- scripts
- MIT airport data license
- .oxlintrc.json
- browser.mjs
- WorkStatus
- p48_throughput.py
- Reusable SVG icon sprite
- vite-env.d.ts
- tsconfig.json
- search_service.py
- index.html
- Web favicon: purple lightning bolt
- React atom logo SVG
- Web HTML entry
- cheapwings
- CheapWings P4.8 — Throughput, Concurrency & Reliability Experiment
- provider-feasibility-evidence.md
- p412_pool_benchmark.py
- json
- ProviderFailure
- P4.5 UI/UX handover, intake and fixes
- provider_failure
- 19. Python Tech Stack Decision, Long-Running Jobs, and Cross-Platform Integration
- P4.8 — Provider interval benchmark and scheduling plan (2026-11-10)
- FlightFinder — Architecture & Design Review Handoff
- 17. Mandatory Multi-Provider Aggregation Architecture (restored; mandatory)
- 12. MVP Milestones and Checkpoints
- test_locations.py
- test_p48_failures.py
- 18. Web + Native iOS Product Design
- 1. Product Intent, Requirements, and Non-Goals
- 2. Proposed Search Experience / UX
- 3. Candidate Data Sources and Due-Diligence Notes
- 15. Mandatory Deliverables from the Reviewing Agent
- 5. Search Algorithm, Coverage, and Failure Handling
- 6. Fare Data Model & Comparability
- dependencies
- 11. Minimal Test Plan and Evaluation Matrix
- 20. Mandatory Cross-Platform and Multi-Provider Acceptance Tests
- 4. Architecture Proposal
- 7. Price Verification Policy
- 8. Filtering and Travel Risks
- AGENTS.md
- CLAUDE.md
- MaxStops
- shadow_money.py
- SingleDateRouteQuery
- 04 — Data, Persistence, and REST API Contracts
- build_location_catalog.py
- Tfs
- pytest
- Foundation
- p412_report.py
- Fli probe — P5.06 spikes S1 (iPhone) and S3 (Swift off-device)
- PackageDescription
- UserAgentMode
- parity.py
- Sendable
- build.sh
- fli-wreq
- cheapwings-money-rs
- cheapwings-money-rs

## God Nodes (most connected - your core abstractions)
1. `Repository` - 113 edges
2. `ProviderFailure` - 99 edges
3. `FakeProvider` - 94 edges
4. `Registration` - 94 edges
5. `JobRunner` - 66 edges
6. `SearchQuery` - 48 edges
7. `now_ms()` - 42 edges
8. `Offer` - 40 edges
9. `results_projection()` - 40 edges
10. `SingleDateRouteQuery` - 38 edges

## Surprising Connections (you probably didn't know these)
- `19.4 Typed provider contract and canonical behavior` --references--> `SingleDateRouteQuery`  [INFERRED]
  docs/reference/V4_FULL_DESIGN_REFERENCE.md → backend/src/cheapwings/providers/base.py
- `3. Native engine design and module ownership` --references--> `Money`  [INFERRED]
  docs/log/p5.05.md → backend/src/cheapwings/domain/money.py
- `17.2 Separate itinerary from offer` --references--> `Itinerary`  [INFERRED]
  docs/reference/V4_FULL_DESIGN_REFERENCE.md → backend/src/cheapwings/domain/itinerary.py
- `19.5 Durable job architecture for searches that take minutes` --references--> `WorkItem`  [INFERRED]
  docs/reference/V4_FULL_DESIGN_REFERENCE.md → backend/src/cheapwings/storage/models.py
- `Current code audit — implications for caching` --references--> `SingleDateRouteQuery`  [INFERRED]
  docs/log/research-cache-p4.6-p4.7.md → backend/src/cheapwings/providers/base.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Planned SwiftUI shares backend contract and durable recovery** — docs_05_web_and_native_ios_swiftui_plan, docs_06_implementation_checkpoints_p5, readme_ios_planned [EXTRACTED 1.00]
- **Exact identity, exact money and unknown-safe rankings** — docs_03_providers_aggregation_pricing_itinerary_offer_identity, docs_03_providers_aggregation_pricing_decimal_money_fx, docs_01_product_requirements_ux_safe_and_advertised_rankings, docs_04_data_and_api_contracts_three_valued_unknowns [INFERRED 0.85]
- **Canonical fare evidence remains conservative across adapters and clients** — docs_03_providers_aggregation_pricing_money, docs_04_data_and_api_contracts_three_valued, docs_log_p4_11_fare_limits, readme_safe_ranking [INFERRED 0.95]

## Communities (127 total, 31 thin omitted)

### Community 0 - "Repository"
Cohesion: 0.05
Nodes (119): DispatchFailure, JobRunner, FakeProvider, Registration, write_session(), FareQuote, ProviderState, WorkAttempt (+111 more)

### Community 1 - ".run"
Cohesion: 0.15
Nodes (5): DecodeError, .description, partialPayload, schemaChanged, Page

### Community 2 - "Money"
Cohesion: 0.19
Nodes (6): Money, test_cannot_compare_different_currencies(), test_idr_has_zero_minor_units(), test_money_rejects_float(), test_money_requires_known_currency_for_minor_units(), test_usd_has_two_minor_units()

### Community 3 - "test_octotrip.py"
Cohesion: 0.13
Nodes (14): OctotripProvider, test_octotrip_429_stops_unsent_peer_http(), test_octotrip_gate_covers_initialization_across_three_sessions(), respond(), payload(), query(), test_bad_source_values_fail_or_disable_navigation(), test_mcp_returns_on_matching_event_without_waiting_for_stream_close() (+6 more)

### Community 4 - "test_p49_review.py"
Cohesion: 0.16
Nodes (17): ReviewDispatcher, ReviewRepository, TimedFake, drain(), max_overlap(), query(), test_cooldown_occupies_no_execution_slot(), test_database_failure_surfaces_instead_of_silent_worker_loss() (+9 more)

### Community 5 - "swoop.py"
Cohesion: 0.10
Nodes (16): airport_transfers(), Offer, FlightSegment, ProviderCapabilities, ProviderRepriceResult, ProviderSearchResult, RepriceRequest, aware_iso() (+8 more)

### Community 6 - "base"
Cohesion: 0.07
Nodes (28): CODE_SIGN_STYLE, CURRENT_PROJECT_VERSION, GENERATE_INFOPLIST_FILE, INFOPLIST_KEY_UILaunchScreen_Generation, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPad, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPhone, MARKETING_VERSION, PRODUCT_BUNDLE_IDENTIFIER (+20 more)

### Community 7 - "sqlalchemy"
Cohesion: 0.14
Nodes (7): upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade()

### Community 8 - "P46ResultsWorkspace.tsx"
Cohesion: 0.13
Nodes (29): PriceStatus, PublicItinerary, PublicOffer, FareRiskNotice(), formatDuration(), ItineraryCard(), BAG_LABEL, COMPARISON_LABEL (+21 more)

### Community 9 - "money-pyo3/src/lib.rs"
Cohesion: 0.21
Nodes (8): as_minor_units(), cheapwings_money_rs(), exponent(), EXPONENTS, from_minor_units(), fx_convert(), minor_unit_exponent(), parse()

### Community 10 - "test_fli.py"
Cohesion: 0.19
Nodes (14): decoder(), payload(), provider(), query(), test_c3_real_threads_overlap_and_cancel_retains_physical_capacity(), fetch(), test_challenge_redirect_is_not_followed(), test_exact_prices_identity_and_conservative_evidence() (+6 more)

### Community 11 - "routes.py"
Cohesion: 0.14
Nodes (3): CapacityExceeded, ResultsExpired, 4. Port-vs-drop matrix

### Community 12 - "App.tsx"
Cohesion: 0.13
Nodes (23): api, ApiError, BASE_URL, request(), TERMINAL_STATUSES, errorMessage(), getOwnerToken(), setOwnerToken() (+15 more)

### Community 13 - "StatusVisuals.tsx"
Cohesion: 0.27
Nodes (10): ProviderProgress, WorkerPool, LABEL, P46SearchProgress(), PoolGauge(), ProviderBars(), SEGMENTS, SOURCE_NAMES (+2 more)

### Community 14 - "06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria"
Cohesion: 0.12
Nodes (16): Provider feasibility and permission gate, 05 — Web + Native iOS Client Implementation, Polling and recovery design, Web first iOS second, Native SwiftUI implementation plan, Web and SwiftUI share remote search engine, 06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria, Fundamental incompatibility escalation (+8 more)

### Community 15 - "minor_unit_exponent"
Cohesion: 0.13
Nodes (8): minor_unit_exponent(), UnknownCurrencyError, test_fx_snapshot_converts(), Decision-rule status (P5.05 §7), Findings, P5.06 — Native engine spikes (S1–S4), Reproduce, Results

### Community 16 - "CheapWings"
Cohesion: 0.11
Nodes (26): Synthetic browser regressions, CheapWings web, React TypeScript Vite thin client, Runtime private access, Memory-only web owner token, Intercepted Playwright browser regression suite, React Vite thin client, Durable job and work state (+18 more)

### Community 17 - "catalog.py"
Cohesion: 0.16
Nodes (4): fold(), LocationCatalog, MajorResolution, MajorSelection

### Community 18 - "test_api.py"
Cohesion: 0.11
Nodes (27): Settings, default_registry(), require_current_schema(), main(), worker_lock(), client_for(), request_data(), test_auth_and_remote_boundary() (+19 more)

### Community 19 - "WORK_LOG.md — Current State (keep under ~80 lines)"
Cohesion: 0.10
Nodes (23): Canonical evidence-preserving extensions, Pre-restructure WORK_LOG header (baseline, full tracker, ledger, summary, deviations), 2026-11-09 empty-repo baseline, Historical initial repository and toolchain, Pre-restructure phase summary, FlightFinder renamed CheapWings, Owner acceptance and merge4c98386, Evidence and phase-history index (+15 more)

### Community 20 - "Provider and result-cache research (2026-11-10)"
Cohesion: 0.06
Nodes (33): request_snapshot(), Cache and OctoTrip implementation kickoff (2026-11-10), Current code audit — implications for caching, Dated provider evaluation — primary sources, not production approval, Final live acceptance and handover — cache + OctoTrip, Hosted endpoint preflight — actual observations and limits, Implementation checkpoint — durable cache and backend selection (in progress), Live owner search — cross-provider overlap confirmed (2026-11-10) (+25 more)

### Community 21 - "Experiment"
Cohesion: 0.11
Nodes (7): post(), wrap(), observed(), test_octotrip_three_sessions_share_one_http_gate(), session(), test_response_timing_preserves_stream_bytes(), respond()

### Community 22 - "SwoopProvider"
Cohesion: 0.17
Nodes (15): SourceEvidence, ItinerarySummary, FXSnapshot, SkiplaggedProvider, SwoopProvider, load(), query(), test_missing_zone_retains_unmatched_summary() (+7 more)

### Community 23 - "types.ts"
Cohesion: 0.10
Nodes (17): AirportTransfer, ComparisonStatus, Coverage, ExpiredObservation, IdentityConfidence, Job, JobPhase, JobStatus (+9 more)

### Community 24 - "SearchForm.tsx"
Cohesion: 0.17
Nodes (17): Currency, ProviderCapability, SearchRequest, AirportMultiSelect(), Props, Props, SearchForm(), todayIso() (+9 more)

### Community 25 - "Itinerary"
Cohesion: 0.15
Nodes (12): compute_fingerprint(), Itinerary, segments(), test_display_names_do_not_change_itinerary_fingerprint(), test_explicit_airport_change_retains_flight_identity_without_fake_leg(), test_undeclared_or_mismatched_airport_changes_stay_invalid(), _seg(), test_different_connections_produce_different_fingerprints() (+4 more)

### Community 27 - ".search"
Cohesion: 0.41
Nodes (7): _query(), test_fake_provider_labels_prices_as_synthetic(), test_fake_provider_respects_idr_zero_minor_units(), test_fake_provider_respects_include_basic_economy_false(), test_fake_provider_returns_deterministic_results(), test_fake_provider_scripted_empty_is_distinct_from_failure(), test_fake_provider_scripted_failure_is_not_empty_success()

### Community 28 - "package.json"
Cohesion: 0.13
Nodes (19): devDependencies, oxlint@^1.90.0, @types/node@^24.19.2, @types/react@^19.3.0, @types/react-dom@^19.3.0, typescript@~7.0.2, vite@^8.3.6, @vitejs/plugin-react@^6.1.2 (+11 more)

### Community 29 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 30 - "P5.05 — Native iOS search engine feasibility analysis"
Cohesion: 0.20
Nodes (10): 10. Sources, facts and open questions, 1. Executive verdict, 2. Provider compatibility matrix, 3. Native engine design and module ownership, 5. Background / foreground behaviour (iOS), 6. Risk register (likelihood × impact, 1–5), 7. Experiment plan (proposal; nothing run; each needs owner approval), 8. Architecture decision record (+2 more)

### Community 31 - "repository.py"
Cohesion: 0.09
Nodes (31): cache_key(), CacheRepository, without_handles(), Base, FXRow, ItineraryRow, OperationAttempt, ProviderOperation (+23 more)

### Community 32 - "p412-browser.mjs"
Cohesion: 0.17
Nodes (9): playwright@^1.65.0, dist, evidence, shots, dist, dist, job, pool (+1 more)

### Community 33 - "compilerOptions"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 34 - "P4.10 — Smart location selection"
Cohesion: 0.16
Nodes (17): Exhaustive combination coverage, P4.10 historical offline acceptance, Backend authoritative Major resolution, Typed Major backend authority, Legacy IATA caller compatibility, P4.10 — Smart location selection, Catalog limitations, P4.10 staged localhost and authorized live wiring (+9 more)

### Community 35 - "06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria"
Cohesion: 0.11
Nodes (17): Bounded blocking provider execution, API application domain dependency boundaries, Dependency boundary, 02 — System Architecture and Runtime Boundaries, Capability-driven provider abstraction, Provider capability protocols, Scheduler design requirements, Coverage and terminal statuses (+9 more)

### Community 36 - "03 — Provider Feasibility, Multi-Provider Aggregation, and Fare Accuracy"
Cohesion: 0.17
Nodes (13): Exact decimal money and FX provenance, 03 — Provider Feasibility, Multi-Provider Aggregation, and Fare Accuracy, Normalized provider error taxonomy, Itinerary versus seller offer, Conservative itinerary identity and separate fare offers, Comparable exact money, Typed provider failures versus successful empty, P0 provider feasibility gate (+5 more)

### Community 37 - "08 — Starting Prompt for a Local Coding Agent"
Cohesion: 0.18
Nodes (9): Authorized task boundaries, Preserve current baseline, 08 — Starting Prompt for a Local Coding Agent, Implementation invariants, Single reporting location, Documentation precedence, CheapWings — Worker Implementation Handoff, Approved implementation handoff (+1 more)

### Community 38 - "BoundedCall"
Cohesion: 0.08
Nodes (20): BoundedCall, __init__(), test_bounded_swoop_executor_c3_has_actual_overlap_and_no_queue(), __init__(), __init__(), __init__(), 2. Implementation, 3. Configuration review (+12 more)

### Community 39 - "fli-wreq/src/lib.rs"
Cohesion: 0.21
Nodes (7): MAX_BODY, wreq_fetch(), WreqError, Build, Request, TooLarge, WreqResponse

### Community 40 - "P4.11 — Fli as a fourth provider"
Cohesion: 0.11
Nodes (19): Historical usable quote verification, P4.11 — Fli as a fourth provider, Truthful failure and cache semantics, Fourth provider Fli public Google Flights page, P4.11 acceptance evidence, Explicit HTTP2 transport, Indicative Google quotes and generic search links, Historical HTTP2 live measurements (+11 more)

### Community 41 - "contracts.py"
Cohesion: 0.10
Nodes (29): create_app(), cancel(), capabilities(), create_search(), get_job(), get_results(), health(), worker_pool() (+21 more)

### Community 42 - "p48_intervals.py"
Cohesion: 0.14
Nodes (7): Measurements, ObservedProvider, observers(), make_send(), observed(), post(), utc()

### Community 43 - "pathlib"
Cohesion: 0.16
Nodes (9): main(), main(), main(), run(), _utc_now_iso(), main(), run(), _to_jsonable() (+1 more)

### Community 44 - "ProbeResult"
Cohesion: 0.33
Nodes (3): FliProbe, ProbeResult, .summary

### Community 45 - "expand_routes_and_dates"
Cohesion: 0.35
Nodes (7): expand_routes_and_dates(), RouteDateCombo, _query(), test_1x3x9_expands_to_27_combinations(), test_combos_are_unique_and_deterministic_order(), test_duplicate_input_codes_are_deduplicated_before_expansion(), test_same_origin_destination_pair_is_skipped()

### Community 46 - "01 — Product Requirements, Rules, and UX Acceptance"
Cohesion: 0.22
Nodes (10): Accessible responsive UI, 01 — Product Requirements, Rules, and UX Acceptance, One-way adult economy flight finder, Flexible one-way finder scope, Query coverage differs from inventory completeness, Conservative fare ranking, Safe Best checked and Lowest advertised views, Honest results states (+2 more)

### Community 47 - "p46-browser.mjs"
Cohesion: 0.28
Nodes (6): all, dist, job, offer(), richEntries, trip()

### Community 48 - "Outcome"
Cohesion: 0.14
Nodes (13): isAllowedRedirect(), Outcome, blockedRedirect, blockedSorry, blockedTraffic, crossCheckFailed, httpError, .mustStop (+5 more)

### Community 49 - "test_swoop_rpc.py"
Cohesion: 0.23
Nodes (7): obj_dict(), parse_search_response(), search(), test_adapter_rejects_short_error_before_normalization(), test_missing_or_malformed_payload_is_not_empty_success(), test_short_rpc_error_is_not_empty_success(), test_valid_empty_with_metadata_frame_is_preserved()

### Community 50 - "p45-browser.mjs"
Cohesion: 0.33
Nodes (5): baseJob, commonOffer, dist, itinerary, query

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

### Community 55 - "WorkStatus"
Cohesion: 0.11
Nodes (21): main(), run_demo(), CoverageEntry, unique_covered_combinations(), WorkStatus, AirportTransfer, build_itinerary(), ItineraryGroup (+13 more)

### Community 56 - "p48_throughput.py"
Cohesion: 0.11
Nodes (11): live_guard(), batch(), emit(), Experiment, main(), provider_run(), migrated(), peak() (+3 more)

### Community 57 - "Reusable SVG icon sprite"
Cohesion: 0.67
Nodes (3): Bluesky, Discord, GitHub and X logos, Reusable SVG icon sprite, Purple documentation and social profile icons

### Community 60 - "search_service.py"
Cohesion: 0.16
Nodes (20): PublicOffer, public_offer(), shortlist(), ComparisonStatus, LinkScope, PriceStatus, ProviderErrorCode, ThreeValued (+12 more)

### Community 75 - "CheapWings P4.8 — Throughput, Concurrency & Reliability Experiment"
Cohesion: 0.12
Nodes (16): Alternative architecture assessment, Authorization and method, CheapWings P4.8 — Throughput, Concurrency & Reliability Experiment, Experiment A — completed live results, Experiment B — offline Python scheduler stress, Experiment C — offline overlapping failure injection, Follow-up — requested C3/1s trials and swoop retry (2026-11-11 Jakarta), Follow-up sanitized per-search ledger (+8 more)

### Community 76 - "provider-feasibility-evidence.md"
Cohesion: 0.13
Nodes (15): Claims vs observed, Claims vs observed, Combined P0 gate outcome, Fields present / absent (for canonical domain mapping), Follow-up probe items, Legal/compliance note (the real risk for swoop), Live sample (redacted selector/links kept short; full in fixture), Owner decisions (resolved 2026-11-09, per `docs/06` stop/escalation rule) (+7 more)

### Community 77 - "p412_pool_benchmark.py"
Cohesion: 0.21
Nodes (10): main(), migrated(), peak(), quantile(), query(), reg(), scenario(), summarize() (+2 more)

### Community 78 - "json"
Cohesion: 0.10
Nodes (12): DispatchDeferred, database(), append_result(), main(), MeasuredProduction, migrated(), quantile(), replay_latencies() (+4 more)

### Community 79 - "ProviderFailure"
Cohesion: 0.09
Nodes (16): ProviderFailure, json_payload(), exact_http_client(), observe(), ExactCapture, FliProvider, HttpStartGate, retry_after() (+8 more)

### Community 80 - "P4.5 UI/UX handover, intake and fixes"
Cohesion: 0.14
Nodes (17): P2–P4 implementation log, Historical CGK to CTS cancelled review, P2 recorded acceptance, P3 adapter normalization and acceptance, P4 React implementation, P4 typed client and polling reliability, Polling effects and stale-page fencing, Historical review follow-ups (+9 more)

### Community 81 - "provider_failure"
Cohesion: 0.13
Nodes (14): provider_failure(), test_network_timeout_classification_in_mcp_group(), Checkpoints 4–5 — implementation and offline verification, Confirmed runtime cause and correction — 2026-11-11, Latest local live search outcome — 2026-11-11, Local live-site wiring — 2026-11-11, Merge status correction — 2026-11-11, Owner merge handoff — 2026-11-11 (+6 more)

### Community 82 - "19. Python Tech Stack Decision, Long-Running Jobs, and Cross-Platform Integration"
Cohesion: 0.14
Nodes (14): 19.10 Native iOS design and lifecycle, 19.11 Deployment and operational risk, 19.12 Technology and provider review verdict, 19.1 Approved direction and rationale, 19.2 Why Python fits the workload, 19.3 Dependency selection and explicit constraints, 19.4 Typed provider contract and canonical behavior, 19.5 Durable job architecture for searches that take minutes (+6 more)

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
Cohesion: 0.16
Nodes (13): resolve_location(), plan_scope(), catalog(), selection(), test_ambiguous_cities_keep_distinct_ids_and_geography(), test_boundary_and_overlap_match_expansion(), test_catalog_rejects_inconsistent_data(), test_lookup() (+5 more)

### Community 88 - "test_p48_failures.py"
Cohesion: 0.10
Nodes (8): lifespan(), fixture(), engine(), migrate(), query(), live_guard(), main(), main()

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

### Community 96 - "dependencies"
Cohesion: 0.50
Nodes (4): dependencies, react@^19.3.1, react-dom@^19.3.1, react-dom

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

### Community 107 - "shadow_money.py"
Cohesion: 0.25
Nodes (6): pytest_configure(), as_minor_units(), convert(), from_minor_units(), minor_unit_exponent(), _shadow()

### Community 108 - "SingleDateRouteQuery"
Cohesion: 0.29
Nodes (4): SearchProvider, SingleDateRouteQuery, offer_from_row(), VerificationRepository

### Community 109 - "04 — Data, Persistence, and REST API Contracts"
Cohesion: 0.20
Nodes (10): Same-offer exact repricing, Authentication and secret boundary, Canonical Money Itinerary Offer Coverage, 04 — Data, Persistence, and REST API Contracts, Normative versioned REST design, Normative versioned REST v1 and canonical DTOs, SQLite persistence schema direction, Unknown is not false (+2 more)

### Community 112 - "pytest"
Cohesion: 0.49
Nodes (8): _base(), test_include_hidden_city_defaults_false_and_does_not_silently_flip(), test_rejects_excessive_combination_count(), test_rejects_invalid_iata(), test_rejects_multi_adult_in_mvp(), test_rejects_reversed_dates(), test_rejects_roundtrip_in_mvp(), test_rejects_same_origin_and_destination()

### Community 113 - "Foundation"
Cohesion: 0.10
Nodes (10): FliProbe, FliWreq, Foundation, SelfTest, WreqProbe, FliProbeApp, .body, ProbeView (+2 more)

### Community 114 - "p412_report.py"
Cohesion: 0.48
Nodes (4): cell(), fmt(), load(), main()

### Community 115 - "Fli probe — P5.06 spikes S1 (iPhone) and S3 (Swift off-device)"
Cohesion: 0.33
Nodes (5): Fli probe — P5.06 spikes S1 (iPhone) and S3 (Swift off-device), Offline check (no network), S1 — physical iPhone (needs full Xcode, owner-approved live requests), S3 — Swift off-device (macOS pre-check), What this does not do

### Community 117 - "UserAgentMode"
Cohesion: 0.20
Nodes (9): UserAgentMode, chromeDesktop, .header, safariIOS, safariIPad, system, Transport, urlSession (+1 more)

### Community 118 - "parity.py"
Cohesion: 0.32
Nodes (3): check(), py_convert(), same()

### Community 119 - "Sendable"
Cohesion: 0.48
Nodes (3): Decoded, Leg, Offer

### Community 120 - "build.sh"
Cohesion: 0.33
Nodes (5): DEVELOPER_DIR, IPHONEOS_DEPLOYMENT_TARGET, MACOSX_DEPLOYMENT_TARGET, PATH, build.sh script

## Knowledge Gaps
- **110 isolated node(s):** `system`, `safariIPad`, `safariIOS`, `chromeDesktop`, `.header` (+105 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 713 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **31 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `P4.12 — Shared global resource pool` connect `BoundedCall` to `Repository`, `WORK_LOG.md — Current State (keep under ~80 lines)`, `StatusVisuals.tsx`?**
  _High betweenness centrality (0.184) - this node is a cross-community bridge._
- **Are the 88 inferred relationships involving `Repository` (e.g. with `AirportTransfer` and `IdentityConfidence`) actually correct?**
  _`Repository` has 88 INFERRED edges - model-reasoned connections that need verification._
- **What connects `system`, `safariIPad`, `safariIOS` to the rest of the system?**
  _110 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Repository` be split into smaller, more focused modules?**
  _Cohesion score 0.05027017181713314 - nodes in this community are weakly interconnected._
- **Why does `Search-status visualization (2026-11-12)` connect `StatusVisuals.tsx` to `BoundedCall`?**
  _High betweenness centrality (0.179) - this node is a cross-community bridge._
- **Are the 41 inferred relationships involving `ProviderFailure` (e.g. with `JobRunner` and `ExactCapture`) actually correct?**
  _`ProviderFailure` has 41 INFERRED edges - model-reasoned connections that need verification._
- **Should `.run` be split into smaller, more focused modules?**
  _Cohesion score 0.14855072463768115 - nodes in this community are weakly interconnected._