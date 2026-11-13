# Graph Report - CheapWings  (2026-11-13)

## Corpus Check
- 185 files · ~296,943 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: .jsonl 5, (none) 3, .css 3)

## Summary
- 1714 nodes · 4984 edges · 112 communities (90 shown, 22 thin omitted)
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 1035 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `463d5c4a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Repository
- Registration
- Money
- rate_limit.py
- Measured Production
- skiplagged.py
- test_p48_failures.py
- sqlalchemy
- Itinerary UI
- CacheRepository
- Fli Provider
- routes.py
- Web API Client
- StatusVisuals.tsx
- repository.py
- JobRunner
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
- .close
- test_search_cache.py
- Browser Test Tooling
- tsconfig Node
- P4.10 Locations Log
- REST Contracts Docs
- Provider Feasibility Docs
- 06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria
- Bounded Calls
- test_p3.py
- P4.11 Fli Log
- results_projection
- p48_intervals.py
- provider_probe_swoop.py
- Client Errors
- Route Expansion
- Product Requirements
- P46 Browser Tests
- test_carrier_airport_change.py
- ProviderFailure
- p45-browser.mjs
- Package Scripts
- Location Licenses
- Lint Config
- Browser Fixtures
- WorkStatus
- batch
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
- SingleDateRouteQuery
- P4.5 UI/UX handover, intake and fixes
- P4.9 — Scheduler architecture, implementation and verification
- 19. Python Tech Stack Decision, Long-Running Jobs, and Cross-Platform Integration
- P4.8 — Provider interval benchmark and scheduling plan (2026-11-10)
- FlightFinder — Architecture & Design Review Handoff
- 17. Mandatory Multi-Provider Aggregation Architecture (restored; mandatory)
- 12. MVP Milestones and Checkpoints
- test_locations.py
- fake.py
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
- test_overlap_429_retry_after_and_independent_provider
- SingleDateRouteQuery
- MatchEngine
- p3_live_canary.py
- P4.12 — Shared global resource pool
- build_location_catalog.py

## God Nodes (most connected - your core abstractions)
1. `Registration` - 94 edges
2. `Repository` - 93 edges
3. `ProviderFailure` - 93 edges
4. `FakeProvider` - 76 edges
5. `JobRunner` - 66 edges
6. `now_ms()` - 42 edges
7. `SearchQuery` - 41 edges
8. `Offer` - 37 edges
9. `SingleDateRouteQuery` - 37 edges
10. `create_app()` - 35 edges

## Surprising Connections (you probably didn't know these)
- `2. Implementation` --references--> `BoundedCall`  [INFERRED]
  docs/log/p4.12.md → backend/src/cheapwings/providers/swoop.py
- `19.4 Typed provider contract and canonical behavior` --references--> `SingleDateRouteQuery`  [INFERRED]
  docs/reference/V4_FULL_DESIGN_REFERENCE.md → backend/src/cheapwings/providers/base.py
- `P4.13 follow-up — result persistence cost (2026-11-13, branch `p4.13-finish-persistence`)` --references--> `test_retained_operation_payload_cleared_without_loading_every_operation()`  [INFERRED]
  docs/log/p4.12.md → backend/tests/integration/test_search_cache.py
- `1. Architecture review — P4.9 admission as merged` --references--> `HttpStartGate`  [INFERRED]
  docs/log/p4.12.md → backend/src/cheapwings/providers/rate_limit.py
- `1. Architecture review — P4.9 admission as merged` --references--> `BoundedCall`  [INFERRED]
  docs/log/p4.12.md → backend/src/cheapwings/providers/swoop.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Planned SwiftUI shares backend contract and durable recovery** — docs_05_web_and_native_ios_swiftui_plan, docs_06_implementation_checkpoints_p5, readme_ios_planned [EXTRACTED 1.00]
- **Exact identity, exact money and unknown-safe rankings** — docs_03_providers_aggregation_pricing_itinerary_offer_identity, docs_03_providers_aggregation_pricing_decimal_money_fx, docs_01_product_requirements_ux_safe_and_advertised_rankings, docs_04_data_and_api_contracts_three_valued_unknowns [INFERRED 0.85]
- **Canonical fare evidence remains conservative across adapters and clients** — docs_03_providers_aggregation_pricing_money, docs_04_data_and_api_contracts_three_valued, docs_log_p4_11_fare_limits, readme_safe_ranking [INFERRED 0.95]

## Communities (112 total, 22 thin omitted)

### Community 0 - "Repository"
Cohesion: 0.16
Nodes (30): FakeProvider, FareQuote, Repository, test_airport_change_never_claims_ground_cost_is_known_on_reprice(), reprice(), search(), test_skiplagged_names_stay_summary_metadata_without_invented_flights(), test_surface_change_and_carriers_survive_worker_storage_api() (+22 more)

### Community 1 - "Registration"
Cohesion: 0.13
Nodes (20): Registration, small(), test_actual_start_deadline_and_cooldown_survive_restart(), test_cancel_before_adapter_entry_makes_no_upstream_call(), test_cancelled_late_429_persists_cooldown_without_quotes(), test_continuous_new_jobs_do_not_starve_already_served_jobs(), test_cooldown_between_claim_and_entry_defers_without_spending_attempt(), test_dispatch_database_failure_surfaces() (+12 more)

### Community 2 - "Money"
Cohesion: 0.11
Nodes (10): minor_unit_exponent(), Money, UnknownCurrencyError, CheckingFake, test_cannot_compare_different_currencies(), test_fx_snapshot_converts(), test_idr_has_zero_minor_units(), test_money_rejects_float() (+2 more)

### Community 3 - "rate_limit.py"
Cohesion: 0.13
Nodes (9): exact_http_client(), observe(), ExactCapture, provider_failure(), retry_after(), mcp_search(), test_network_timeout_classification_in_mcp_group(), test_mcp_capture_preserves_sse_decimals() (+1 more)

### Community 4 - "Measured Production"
Cohesion: 0.12
Nodes (20): MeasuredProduction, ReviewDispatcher, ReviewRepository, run_trial(), admit(), TimedFake, drain(), max_overlap() (+12 more)

### Community 5 - "skiplagged.py"
Cohesion: 0.15
Nodes (11): SourceEvidence, FXSnapshot, Offer, aware_iso(), decimal_value(), money(), stable_id(), SkiplaggedProvider (+3 more)

### Community 6 - "test_p48_failures.py"
Cohesion: 0.12
Nodes (4): DispatchDeferred, DispatchFailure, live_guard(), main()

### Community 7 - "sqlalchemy"
Cohesion: 0.14
Nodes (7): upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade()

### Community 8 - "Itinerary UI"
Cohesion: 0.13
Nodes (29): PriceStatus, PublicItinerary, PublicOffer, FareRiskNotice(), formatDuration(), ItineraryCard(), BAG_LABEL, COMPARISON_LABEL (+21 more)

### Community 9 - "CacheRepository"
Cohesion: 0.32
Nodes (3): cache_key(), CacheRepository, without_handles()

### Community 10 - "Fli Provider"
Cohesion: 0.19
Nodes (14): decoder(), payload(), provider(), query(), test_c3_real_threads_overlap_and_cancel_retains_physical_capacity(), fetch(), test_challenge_redirect_is_not_followed(), test_exact_prices_identity_and_conservative_evidence() (+6 more)

### Community 11 - "routes.py"
Cohesion: 0.08
Nodes (17): create_app(), cancel(), create_search(), get_job(), get_results(), health(), lifespan(), resolve_location() (+9 more)

### Community 12 - "Web API Client"
Cohesion: 0.22
Nodes (12): api, SortMode, App(), jobIdFromUrl(), setJobIdInUrl(), ExpiredFareCard(), JobErrorPanel(), ResultSortBar() (+4 more)

### Community 13 - "StatusVisuals.tsx"
Cohesion: 0.26
Nodes (10): ProviderProgress, WorkerPool, LABEL, P46SearchProgress(), PoolGauge(), ProviderBars(), SEGMENTS, SOURCE_NAMES (+2 more)

### Community 14 - "repository.py"
Cohesion: 0.13
Nodes (15): Base, FXRow, ItineraryRow, OperationAttempt, ProviderOperation, ProviderResultCache, ProviderState, QuoteRevision (+7 more)

### Community 15 - "JobRunner"
Cohesion: 0.16
Nodes (15): JobRunner, test_pagination_freezes_incremental_quote_set(), test_fli_real_normalization_api_prices_and_cache(), transport(), test_fli_uses_durable_shared_fetch_cancel_fencing_and_cache(), fetch(), test_missing_fli_payload_is_failure_and_never_cached(), test_cancel_does_not_release_live_global_slot() (+7 more)

### Community 16 - "Architecture Docs"
Cohesion: 0.08
Nodes (33): Synthetic browser regressions, CheapWings web, React TypeScript Vite thin client, Runtime private access, Memory-only web owner token, Intercepted Playwright browser regression suite, React Vite thin client, Bounded blocking provider execution (+25 more)

### Community 17 - "catalog.py"
Cohesion: 0.20
Nodes (4): fold(), LocationCatalog, MajorResolution, MajorSelection

### Community 18 - "asyncio"
Cohesion: 0.14
Nodes (28): Settings, default_registry(), main(), client_for(), request_data(), test_api_scheduler_results_contract(), test_auth_and_remote_boundary(), test_baggage_eligibility_and_snapshot_cursor() (+20 more)

### Community 19 - "WORK_LOG.md — Current State (keep under ~80 lines)"
Cohesion: 0.10
Nodes (24): Canonical evidence-preserving extensions, Pre-restructure WORK_LOG header (baseline, full tracker, ledger, summary, deviations), 2026-11-09 empty-repo baseline, Historical initial repository and toolchain, Pre-restructure phase summary, FlightFinder renamed CheapWings, Owner acceptance and merge4c98386, Evidence and phase-history index (+16 more)

### Community 20 - "Provider and result-cache research (2026-11-10)"
Cohesion: 0.06
Nodes (32): request_snapshot(), Cache and OctoTrip implementation kickoff (2026-11-10), Current code audit — implications for caching, Dated provider evaluation — primary sources, not production approval, Final live acceptance and handover — cache + OctoTrip, Hosted endpoint preflight — actual observations and limits, Implementation checkpoint — durable cache and backend selection (in progress), Live owner search — cross-provider overlap confirmed (2026-11-10) (+24 more)

### Community 21 - "Throughput Experiment"
Cohesion: 0.12
Nodes (8): Experiment, post(), wrap(), observed(), test_octotrip_three_sessions_share_one_http_gate(), session(), test_response_timing_preserves_stream_bytes(), respond()

### Community 22 - "SwoopProvider"
Cohesion: 0.18
Nodes (11): ItinerarySummary, ProviderSearchResult, SearchProvider, SwoopProvider, load(), query(), test_missing_zone_retains_unmatched_summary(), test_skiplagged_exact_money_unknown_fields_and_no_fake_segments() (+3 more)

### Community 23 - "Web Types"
Cohesion: 0.10
Nodes (18): AirportTransfer, ComparisonStatus, Coverage, Created, ExpiredObservation, IdentityConfidence, Job, JobPhase (+10 more)

### Community 24 - "Search Form"
Cohesion: 0.17
Nodes (17): Currency, ProviderCapability, SearchRequest, AirportMultiSelect(), Props, Props, SearchForm(), todayIso() (+9 more)

### Community 25 - "Itinerary"
Cohesion: 0.09
Nodes (21): airport_transfers(), AirportTransfer, compute_fingerprint(), IdentityConfidence, Itinerary, FlightSegment, build_itinerary(), ProviderCapabilities (+13 more)

### Community 26 - "Search Query Model"
Cohesion: 0.18
Nodes (11): QueryValidationError, SearchQuery, test_zero_routes_and_date_changes(), _base(), test_include_hidden_city_defaults_false_and_does_not_silently_flip(), test_rejects_excessive_combination_count(), test_rejects_invalid_iata(), test_rejects_multi_adult_in_mvp() (+3 more)

### Community 27 - "now_ms"
Cohesion: 0.20
Nodes (11): write_session(), now_ms(), test_reprice_job_is_not_starved_by_shared_search_backlog(), test_provider_spacing_is_start_to_start_and_other_source_is_independent(), 5. Benchmark — P4.9 C3 versus P4.12 pool (synthetic), result(), scope(), test_cancelled_result_still_must_preserve_provider_feedback() (+3 more)

### Community 28 - "Web Dev Deps"
Cohesion: 0.13
Nodes (19): devDependencies, oxlint@^1.90.0, @types/node@^24.19.2, @types/react@^19.3.0, @types/react-dom@^19.3.0, typescript@~7.0.2, vite@^8.3.6, @vitejs/plugin-react@^6.1.2 (+11 more)

### Community 29 - "tsconfig App"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 30 - ".close"
Cohesion: 0.28
Nodes (14): Logged, test_blocking_adapter_pool_sized_to_g_uses_real_threads(), search(), test_cooled_provider_stops_starting_and_others_take_the_pool(), test_headroom_lets_late_higher_priority_work_start_immediately(), test_headroom_unused_without_an_available_higher_priority_source(), test_lower_priority_only_gets_slots_higher_tiers_cannot_use(), test_paced_provider_overlaps_with_actual_start_gaps() (+6 more)

### Community 31 - "test_search_cache.py"
Cohesion: 0.13
Nodes (21): Counted, finish(), setup(), test_absolute_retention_deadline_expires_inherited_job_and_purges(), test_additive_migration_preserves_populated_work_attempt_and_quote_history(), test_cache_eviction_bytes_policy_revocation_and_filter_reapplication(), test_cache_reuse_is_independent_of_other_selected_sources(), test_cached_snapshot_keeps_money_times_ids_and_absolute_expiry() (+13 more)

### Community 32 - "Browser Test Tooling"
Cohesion: 0.17
Nodes (9): playwright@^1.65.0, dist, evidence, shots, dist, dist, job, pool (+1 more)

### Community 33 - "tsconfig Node"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 34 - "P4.10 Locations Log"
Cohesion: 0.16
Nodes (17): Exhaustive combination coverage, P4.10 historical offline acceptance, Backend authoritative Major resolution, Typed Major backend authority, Legacy IATA caller compatibility, P4.10 — Smart location selection, Catalog limitations, P4.10 staged localhost and authorized live wiring (+9 more)

### Community 35 - "REST Contracts Docs"
Cohesion: 0.12
Nodes (16): Scheduler design requirements, Authentication and secret boundary, Canonical Money Itinerary Offer Coverage, Coverage and terminal statuses, 04 — Data, Persistence, and REST API Contracts, Normative versioned REST design, Normative versioned REST v1 and canonical DTOs, SQLite persistence schema direction (+8 more)

### Community 36 - "Provider Feasibility Docs"
Cohesion: 0.12
Nodes (17): Exact decimal money and FX provenance, 03 — Provider Feasibility, Multi-Provider Aggregation, and Fare Accuracy, Normalized provider error taxonomy, Itinerary versus seller offer, Conservative itinerary identity and separate fare offers, Comparable exact money, Typed provider failures versus successful empty, P0 provider feasibility gate (+9 more)

### Community 37 - "06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria"
Cohesion: 0.08
Nodes (25): Provider feasibility and permission gate, 05 — Web + Native iOS Client Implementation, Polling and recovery design, Web first iOS second, Native SwiftUI implementation plan, Web and SwiftUI share remote search engine, 06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria, Fundamental incompatibility escalation (+17 more)

### Community 38 - "Bounded Calls"
Cohesion: 0.13
Nodes (9): BoundedCall, __init__(), test_bounded_swoop_executor_c3_has_actual_overlap_and_no_queue(), __init__(), __init__(), __init__(), test_real_thread_slot_retained_on_cancellation(), Synth (+1 more)

### Community 39 - "test_p3.py"
Cohesion: 0.17
Nodes (8): database(), fixture(), test_recorded_real_adapters_api_summary_fx_and_expiry(), engine(), migrate(), query(), migrated(), migrated()

### Community 40 - "P4.11 Fli Log"
Cohesion: 0.11
Nodes (19): Historical usable quote verification, P4.11 — Fli as a fourth provider, Truthful failure and cache semantics, Fourth provider Fli public Google Flights page, P4.11 acceptance evidence, Explicit HTTP2 transport, Indicative Google quotes and generic search links, Historical HTTP2 live measurements (+11 more)

### Community 41 - "results_projection"
Cohesion: 0.13
Nodes (21): capabilities(), worker_pool(), AirportTransfer, Capabilities, Coverage, Created, DTO, ExpiredObservation (+13 more)

### Community 42 - "p48_intervals.py"
Cohesion: 0.15
Nodes (7): Measurements, ObservedProvider, observers(), make_send(), observed(), post(), utc()

### Community 43 - "provider_probe_swoop.py"
Cohesion: 0.53
Nodes (4): main(), run(), _to_jsonable(), _utc_now_iso()

### Community 44 - "Client Errors"
Cohesion: 0.24
Nodes (10): ApiError, BASE_URL, request(), TERMINAL_STATUSES, errorMessage(), getOwnerToken(), setOwnerToken(), Capabilities (+2 more)

### Community 45 - "Route Expansion"
Cohesion: 0.35
Nodes (7): expand_routes_and_dates(), RouteDateCombo, _query(), test_1x3x9_expands_to_27_combinations(), test_combos_are_unique_and_deterministic_order(), test_duplicate_input_codes_are_deduplicated_before_expansion(), test_same_origin_destination_pair_is_skipped()

### Community 46 - "Product Requirements"
Cohesion: 0.22
Nodes (10): Accessible responsive UI, 01 — Product Requirements, Rules, and UX Acceptance, One-way adult economy flight finder, Flexible one-way finder scope, Query coverage differs from inventory completeness, Conservative fare ranking, Safe Best checked and Lowest advertised views, Honest results states (+2 more)

### Community 47 - "P46 Browser Tests"
Cohesion: 0.28
Nodes (6): all, dist, job, offer(), richEntries, trip()

### Community 49 - "ProviderFailure"
Cohesion: 0.10
Nodes (17): ProviderFailure, obj_dict(), FliProvider, local_instant(), parse_search_response(), search(), search(), search() (+9 more)

### Community 50 - "p45-browser.mjs"
Cohesion: 0.33
Nodes (5): baseJob, commonOffer, dist, itinerary, query

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

### Community 55 - "WorkStatus"
Cohesion: 0.19
Nodes (11): main(), run_demo(), CoverageEntry, unique_covered_combinations(), WorkStatus, ScriptedOutcome, _entry(), test_failed_terminal_requires_error_code() (+3 more)

### Community 56 - "batch"
Cohesion: 0.13
Nodes (10): live_guard(), batch(), emit(), main(), provider_run(), migrated(), peak(), percentile() (+2 more)

### Community 57 - "Icon Sprite"
Cohesion: 0.67
Nodes (3): Bluesky, Discord, GitHub and X logos, Reusable SVG icon sprite, Purple documentation and social profile icons

### Community 60 - "test_ranking.py"
Cohesion: 0.23
Nodes (13): ItineraryGroup, best_checked_deal(), _is_safe_for_default_ranking(), lowest_advertised(), RankedOffer, _group(), _offer(), test_hidden_city_excluded_from_default_ranking() (+5 more)

### Community 75 - "CheapWings P4.8 — Throughput, Concurrency & Reliability Experiment"
Cohesion: 0.12
Nodes (16): Alternative architecture assessment, Authorization and method, CheapWings P4.8 — Throughput, Concurrency & Reliability Experiment, Experiment A — completed live results, Experiment B — offline Python scheduler stress, Experiment C — offline overlapping failure injection, Follow-up — requested C3/1s trials and swoop retry (2026-11-11 Jakarta), Follow-up sanitized per-search ledger (+8 more)

### Community 76 - "Provider feasibility evidence"
Cohesion: 0.13
Nodes (15): Claims vs observed, Claims vs observed, Combined P0 gate outcome, Fields present / absent (for canonical domain mapping), Follow-up probe items, Legal/compliance note (the real risk for swoop), Live sample (redacted selector/links kept short; full in fixture), Owner decisions (resolved 2026-11-09, per `docs/06` stop/escalation rule) (+7 more)

### Community 77 - "p412_pool_benchmark.py"
Cohesion: 0.15
Nodes (12): main(), peak(), quantile(), query(), scenario(), summarize(), threads(), cell() (+4 more)

### Community 78 - "json"
Cohesion: 0.09
Nodes (11): append_result(), main(), replay_latencies(), Scenario, scenarios(), main(), main(), main() (+3 more)

### Community 79 - "SingleDateRouteQuery"
Cohesion: 0.10
Nodes (16): json_payload(), OctotripProvider, HttpStartGate, test_octotrip_429_stops_unsent_peer_http(), test_octotrip_gate_covers_initialization_across_three_sessions(), respond(), payload(), query() (+8 more)

### Community 80 - "P4.5 UI/UX handover, intake and fixes"
Cohesion: 0.14
Nodes (17): P2–P4 implementation log, Historical CGK to CTS cancelled review, P2 recorded acceptance, P3 adapter normalization and acceptance, P4 React implementation, P4 typed client and polling reliability, Polling effects and stale-page fencing, Historical review follow-ups (+9 more)

### Community 81 - "P4.9 — Scheduler architecture, implementation and verification"
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
Cohesion: 0.29
Nodes (7): 17.1 Pipeline, 17.3 Provider interface and capabilities, 17.4 Aggregation and ranking rules, 17.5 Isolation, compliance, and extensibility, 17.6 Additional independent reviewer deliverables, 17.7 Acceptance checkpoints, 17. Mandatory Multi-Provider Aggregation Architecture (restored; mandatory)

### Community 86 - "12. MVP Milestones and Checkpoints"
Cohesion: 0.29
Nodes (7): 12. MVP Milestones and Checkpoints, P0 — Provider Feasibility Gate (reviewer first), P1 — CLI / Engine Baseline, P2 — Provider Aggregation and Repricing, P3 — Web UI on versioned backend API, P4 — Reliability and Validation, P5 — Native iOS App (after backend/API is stable)

### Community 87 - "test_locations.py"
Cohesion: 0.18
Nodes (11): plan_scope(), catalog(), selection(), test_ambiguous_cities_keep_distinct_ids_and_geography(), test_boundary_and_overlap_match_expansion(), test_catalog_rejects_inconsistent_data(), test_lookup(), test_major_resolution_and_no_fallback() (+3 more)

### Community 88 - "fake.py"
Cohesion: 0.32
Nodes (7): PublicOffer, shortlist(), ComparisonStatus, LinkScope, PriceStatus, ProviderErrorCode, ThreeValued

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

### Community 105 - "test_overlap_429_retry_after_and_independent_provider"
Cohesion: 0.23
Nodes (13): reg(), drain(), record(), short(), recover(), test_concurrent_claims_under_real_sqlite_lock(), claim(), test_overlap_429_retry_after_and_independent_provider() (+5 more)

### Community 106 - "SingleDateRouteQuery"
Cohesion: 0.31
Nodes (10): SingleDateRouteQuery, test_safe_external_link_policy(), sample(), _query(), test_fake_provider_labels_prices_as_synthetic(), test_fake_provider_respects_idr_zero_minor_units(), test_fake_provider_respects_include_basic_economy_false(), test_fake_provider_returns_deterministic_results() (+2 more)

### Community 107 - "MatchEngine"
Cohesion: 0.45
Nodes (7): MatchEngine, _offer(), _seg(), test_different_connections_are_different_itineraries(), test_duplicate_quote_response_is_idempotent(), test_insufficient_identity_itineraries_never_merge(), test_same_itinerary_two_providers_groups_with_distinct_offers()

### Community 108 - "p3_live_canary.py"
Cohesion: 0.24
Nodes (5): RepriceRequest, offer_from_row(), VerificationRepository, _jsonable(), run()

### Community 109 - "P4.12 — Shared global resource pool"
Cohesion: 0.17
Nodes (12): 2. Implementation, 3. Configuration review, 4. Regression tests, 6. Risk analysis, 7. Recommended production configuration, 8. Owner decisions, Conservative live Fli ladder (owner-approved), Follow-up — priority tiers and low-priority headroom (2026-11-12) (+4 more)

## Knowledge Gaps
- **78 isolated node(s):** `cheapwings`, `API application domain dependency boundaries`, `Snapshot cursor pagination and ranked quote`, `Owner access and request admission`, `Capability-driven provider abstraction` (+73 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 604 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `P4.12 — Shared global resource pool` connect `P4.12 — Shared global resource pool` to `now_ms`, `WORK_LOG.md — Current State (keep under ~80 lines)`, `StatusVisuals.tsx`, `JobRunner`?**
  _High betweenness centrality (0.207) - this node is a cross-community bridge._
- **Are the 90 inferred relationships involving `Registration` (e.g. with `SearchProvider` and `test_api_scheduler_results_contract()`) actually correct?**
  _`Registration` has 90 INFERRED edges - model-reasoned connections that need verification._
- **What connects `cheapwings`, `API application domain dependency boundaries`, `Snapshot cursor pagination and ranked quote` to the rest of the system?**
  _78 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Registration` be split into smaller, more focused modules?**
  _Cohesion score 0.1265597147950089 - nodes in this community are weakly interconnected._
- **Why does `Search-status visualization (2026-11-12)` connect `StatusVisuals.tsx` to `P4.12 — Shared global resource pool`?**
  _High betweenness centrality (0.185) - this node is a cross-community bridge._
- **Are the 68 inferred relationships involving `Repository` (e.g. with `test_pagination_freezes_incremental_quote_set()` and `test_worker_pool_status_counts_shared_once_and_flags_cooldown()`) actually correct?**
  _`Repository` has 68 INFERRED edges - model-reasoned connections that need verification._
- **Should `Money` be split into smaller, more focused modules?**
  _Cohesion score 0.10967741935483871 - nodes in this community are weakly interconnected._