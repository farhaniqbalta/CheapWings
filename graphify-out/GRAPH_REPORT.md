# Graph Report - CheapWings  (2026-11-12)

## Corpus Check
- 181 files · ~294,575 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 14 file(s) not represented in the graph (top: (none) 3, .css 3, .jsonl 3)

## Summary
- 1692 nodes · 5022 edges · 109 communities (82 shown, 27 thin omitted)
- Extraction: 77% EXTRACTED · 23% INFERRED · 0% AMBIGUOUS · INFERRED: 1145 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8918531e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Repository
- swoop.py
- Money
- ProviderFailure
- Measured Production
- Offer
- p49_scheduler_comparison.py
- test_scheduler.py
- Itinerary UI
- JobRunner
- Fli Provider
- p411_fli_live.py
- Web API Client
- 02 — System Architecture and Runtime Boundaries
- create_app
- pathlib
- Architecture Docs
- catalog.py
- asyncio
- WORK_LOG.md — Current State (keep under ~80 lines)
- Provider and result-cache research (2026-11-10)
- Throughput Experiment
- test_p48_scheduler_review.py
- Web Types
- Search Form
- Itinerary
- Search Query Model
- pytest
- Web Dev Deps
- tsconfig App
- Pre-restructure WORK_LOG header (baseline, full tracker, ledger, summary, deviations)
- repository.py
- Browser Test Tooling
- tsconfig Node
- P4.10 Locations Log
- REST Contracts Docs
- Provider Feasibility Docs
- 05 — Web + Native iOS Client Implementation
- Bounded Calls
- test_recorded_real_adapters_api_summary_fx_and_expiry
- P4.11 Fli Log
- results_projection
- p48_intervals.py
- Skiplagged Probe
- Client Errors
- Route Expansion
- Product Requirements
- P46 Browser Tests
- Registration
- Offer
- .execute
- Package Scripts
- Location Licenses
- Lint Config
- Browser Fixtures
- datetime
- batch
- Icon Sprite
- Vite Env Types
- tsconfig Root
- Dispatch Deferred
- Web Entry HTML
- Favicon
- React Logo
- Package Init 65
- Package Init 74
- CheapWings P4.8 — Throughput, Concurrency & Reliability Experiment
- Provider feasibility evidence
- p412_pool_benchmark.py
- test_p48_failures.py
- SingleDateRouteQuery
- P4.5 UI/UX handover, intake and fixes
- P4.9 — Scheduler architecture, implementation and verification
- 19. Python Tech Stack Decision, Long-Running Jobs, and Cross-Platform Integration
- P4.8 — Provider interval benchmark and scheduling plan (2026-11-10)
- FlightFinder — Architecture & Design Review Handoff
- 17. Mandatory Multi-Provider Aggregation Architecture (restored; mandatory)
- 12. MVP Milestones and Checkpoints
- test_locations.py
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
- query.py
- build_location_catalog.py

## God Nodes (most connected - your core abstractions)
1. `Repository` - 111 edges
2. `ProviderFailure` - 96 edges
3. `Registration` - 92 edges
4. `FakeProvider` - 90 edges
5. `JobRunner` - 63 edges
6. `SearchQuery` - 43 edges
7. `Offer` - 41 edges
8. `results_projection()` - 40 edges
9. `now_ms()` - 38 edges
10. `SingleDateRouteQuery` - 36 edges

## Surprising Connections (you probably didn't know these)
- `19.4 Typed provider contract and canonical behavior` --references--> `SingleDateRouteQuery`  [INFERRED]
  docs/reference/V4_FULL_DESIGN_REFERENCE.md → backend/src/cheapwings/providers/base.py
- `Skiplagged cooldown and active-work display follow-up — 2026-11-11` --references--> `provider_failure()`  [INFERRED]
  docs/log/p4.9.md → backend/src/cheapwings/providers/rate_limit.py
- `1. Architecture review — P4.9 admission as merged` --references--> `HttpStartGate`  [INFERRED]
  docs/log/p4.12.md → backend/src/cheapwings/providers/rate_limit.py
- `1. Architecture review — P4.9 admission as merged` --references--> `BoundedCall`  [INFERRED]
  docs/log/p4.12.md → backend/src/cheapwings/providers/swoop.py
- `2. Implementation` --references--> `BoundedCall`  [INFERRED]
  docs/log/p4.12.md → backend/src/cheapwings/providers/swoop.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Planned SwiftUI shares backend contract and durable recovery** — docs_05_web_and_native_ios_swiftui_plan, docs_06_implementation_checkpoints_p5, readme_ios_planned [EXTRACTED 1.00]
- **Exact identity, exact money and unknown-safe rankings** — docs_03_providers_aggregation_pricing_itinerary_offer_identity, docs_03_providers_aggregation_pricing_decimal_money_fx, docs_01_product_requirements_ux_safe_and_advertised_rankings, docs_04_data_and_api_contracts_three_valued_unknowns [INFERRED 0.85]
- **Canonical fare evidence remains conservative across adapters and clients** — docs_03_providers_aggregation_pricing_money, docs_04_data_and_api_contracts_three_valued, docs_log_p4_11_fare_limits, readme_safe_ranking [INFERRED 0.95]

## Communities (109 total, 27 thin omitted)

### Community 0 - "Repository"
Cohesion: 0.13
Nodes (29): write_session(), ProviderState, WorkAttempt, WorkItem, now_ms(), Repository, test_actual_start_deadline_and_cooldown_survive_restart(), test_cancel_before_adapter_entry_makes_no_upstream_call() (+21 more)

### Community 1 - "swoop.py"
Cohesion: 0.14
Nodes (10): airport_transfers(), FlightSegment, ProviderCapabilities, ProviderRepriceResult, RepriceRequest, obj_dict(), airport_zone(), _airports() (+2 more)

### Community 2 - "Money"
Cohesion: 0.10
Nodes (16): minor_unit_exponent(), Money, UnknownCurrencyError, _query(), test_fake_provider_labels_prices_as_synthetic(), test_fake_provider_respects_idr_zero_minor_units(), test_fake_provider_respects_include_basic_economy_false(), test_fake_provider_returns_deterministic_results() (+8 more)

### Community 3 - "ProviderFailure"
Cohesion: 0.10
Nodes (17): ProviderFailure, exact_http_client(), observe(), ExactCapture, FliProvider, provider_failure(), retry_after(), mcp_search() (+9 more)

### Community 4 - "Measured Production"
Cohesion: 0.16
Nodes (17): ReviewDispatcher, ReviewRepository, TimedFake, drain(), max_overlap(), query(), test_cooldown_occupies_no_execution_slot(), test_database_failure_surfaces_instead_of_silent_worker_loss() (+9 more)

### Community 5 - "Offer"
Cohesion: 0.17
Nodes (19): shortlist(), ComparisonStatus, LinkScope, PriceStatus, ProviderErrorCode, ThreeValued, ItineraryGroup, best_checked_deal() (+11 more)

### Community 6 - "p49_scheduler_comparison.py"
Cohesion: 0.10
Nodes (12): database(), migrated(), append_result(), main(), MeasuredProduction, migrated(), quantile(), replay_latencies() (+4 more)

### Community 7 - "test_scheduler.py"
Cohesion: 0.16
Nodes (24): Logged, test_blocking_adapter_pool_sized_to_g_uses_real_threads(), search(), test_cooled_provider_stops_starting_and_others_take_the_pool(), test_headroom_lets_late_higher_priority_work_start_immediately(), test_headroom_unused_without_an_available_higher_priority_source(), test_lower_priority_only_gets_slots_higher_tiers_cannot_use(), test_paced_provider_overlaps_with_actual_start_gaps() (+16 more)

### Community 8 - "Itinerary UI"
Cohesion: 0.15
Nodes (27): PublicOffer, FareRiskNotice(), formatDuration(), ItineraryCard(), BAG_LABEL, COMPARISON_LABEL, describeLink(), OfferList() (+19 more)

### Community 9 - "JobRunner"
Cohesion: 0.20
Nodes (12): test_fli_real_normalization_api_prices_and_cache(), transport(), test_fli_uses_durable_shared_fetch_cancel_fencing_and_cache(), test_missing_fli_payload_is_failure_and_never_cached(), test_short_source_expiry_preserves_other_source_and_running_job(), test_cancelled_late_429_persists_cooldown_without_quotes(), test_provider_specific_timeout_extends_lease_without_changing_other_sources(), test_cancel_fences_late_response_preserves_success() (+4 more)

### Community 10 - "Fli Provider"
Cohesion: 0.11
Nodes (20): parse_search_response(), fixture(), decoder(), payload(), provider(), query(), test_c3_real_threads_overlap_and_cancel_retains_physical_capacity(), fetch() (+12 more)

### Community 11 - "p411_fli_live.py"
Cohesion: 0.19
Nodes (3): live_guard(), main(), trial()

### Community 12 - "Web API Client"
Cohesion: 0.20
Nodes (13): api, SortMode, App(), jobIdFromUrl(), setJobIdInUrl(), ExpiredFareCard(), JobErrorPanel(), P46SearchProgress() (+5 more)

### Community 13 - "02 — System Architecture and Runtime Boundaries"
Cohesion: 0.18
Nodes (11): Bounded blocking provider execution, API application domain dependency boundaries, Dependency boundary, 02 — System Architecture and Runtime Boundaries, Durable job and work state, Capability-driven provider abstraction, Provider capability protocols, P2 durable storage and REST implementation (+3 more)

### Community 14 - "create_app"
Cohesion: 0.20
Nodes (7): create_app(), cancel(), get_job(), get_results(), health(), _exact_reprice_count(), status_projection()

### Community 15 - "pathlib"
Cohesion: 0.25
Nodes (4): cell(), fmt(), load(), main()

### Community 16 - "Architecture Docs"
Cohesion: 0.13
Nodes (22): Synthetic browser regressions, CheapWings web, React TypeScript Vite thin client, Runtime private access, Memory-only web owner token, Intercepted Playwright browser regression suite, React Vite thin client, Fare evidence tiers (+14 more)

### Community 17 - "catalog.py"
Cohesion: 0.20
Nodes (4): fold(), LocationCatalog, MajorResolution, MajorSelection

### Community 18 - "asyncio"
Cohesion: 0.07
Nodes (30): Settings, default_registry(), require_current_schema(), ResultsExpired, main(), worker_lock(), client_for(), request_data() (+22 more)

### Community 19 - "WORK_LOG.md — Current State (keep under ~80 lines)"
Cohesion: 0.10
Nodes (23): Authorized task boundaries, Preserve current baseline, 08 — Starting Prompt for a Local Coding Agent, Implementation invariants, Single reporting location, Evidence and phase-history index, Dated history is evidence rather than active instructions, 2026-11-11 documentation cleanup (+15 more)

### Community 20 - "Provider and result-cache research (2026-11-10)"
Cohesion: 0.06
Nodes (33): request_snapshot(), Cache and OctoTrip implementation kickoff (2026-11-10), Current code audit — implications for caching, Dated provider evaluation — primary sources, not production approval, Final live acceptance and handover — cache + OctoTrip, Hosted endpoint preflight — actual observations and limits, Implementation checkpoint — durable cache and backend selection (in progress), Live owner search — cross-provider overlap confirmed (2026-11-10) (+25 more)

### Community 21 - "Throughput Experiment"
Cohesion: 0.11
Nodes (8): Experiment, post(), wrap(), observed(), test_octotrip_three_sessions_share_one_http_gate(), session(), test_response_timing_preserves_stream_bytes(), respond()

### Community 22 - "test_p48_scheduler_review.py"
Cohesion: 0.33
Nodes (5): fetch(), result(), scope(), test_restart_preserves_spacing_and_provider_cooldown(), test_unequal_intervals_short_and_long_calls()

### Community 23 - "Web Types"
Cohesion: 0.09
Nodes (20): AirportTransfer, ComparisonStatus, Coverage, ExpiredObservation, IdentityConfidence, Job, JobPhase, JobStatus (+12 more)

### Community 24 - "Search Form"
Cohesion: 0.17
Nodes (17): Currency, ProviderCapability, SearchRequest, AirportMultiSelect(), Props, Props, SearchForm(), todayIso() (+9 more)

### Community 25 - "Itinerary"
Cohesion: 0.10
Nodes (24): main(), run_demo(), AirportTransfer, compute_fingerprint(), IdentityConfidence, Itinerary, build_itinerary(), MatchEngine (+16 more)

### Community 27 - "pytest"
Cohesion: 0.49
Nodes (8): _base(), test_include_hidden_city_defaults_false_and_does_not_silently_flip(), test_rejects_excessive_combination_count(), test_rejects_invalid_iata(), test_rejects_multi_adult_in_mvp(), test_rejects_reversed_dates(), test_rejects_roundtrip_in_mvp(), test_rejects_same_origin_and_destination()

### Community 28 - "Web Dev Deps"
Cohesion: 0.13
Nodes (19): devDependencies, oxlint@^1.90.0, @types/node@^24.19.2, @types/react@^19.3.0, @types/react-dom@^19.3.0, typescript@~7.0.2, vite@^8.3.6, @vitejs/plugin-react@^6.1.2 (+11 more)

### Community 29 - "tsconfig App"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 30 - "Pre-restructure WORK_LOG header (baseline, full tracker, ledger, summary, deviations)"
Cohesion: 0.22
Nodes (9): Canonical evidence-preserving extensions, Pre-restructure WORK_LOG header (baseline, full tracker, ledger, summary, deviations), 2026-11-09 empty-repo baseline, Historical initial repository and toolchain, Pre-restructure phase summary, FlightFinder renamed CheapWings, Owner acceptance and merge4c98386, Dated evidence index (+1 more)

### Community 31 - "repository.py"
Cohesion: 0.05
Nodes (43): upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), lifespan() (+35 more)

### Community 32 - "Browser Test Tooling"
Cohesion: 0.16
Nodes (11): playwright@^1.65.0, dist, evidence, shots, dist, baseJob, commonOffer, dist (+3 more)

### Community 33 - "tsconfig Node"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 34 - "P4.10 Locations Log"
Cohesion: 0.16
Nodes (17): Exhaustive combination coverage, P4.10 historical offline acceptance, Backend authoritative Major resolution, Typed Major backend authority, Legacy IATA caller compatibility, P4.10 — Smart location selection, Catalog limitations, P4.10 staged localhost and authorized live wiring (+9 more)

### Community 35 - "REST Contracts Docs"
Cohesion: 0.09
Nodes (22): Scheduler design requirements, Same-offer exact repricing, Authentication and secret boundary, Canonical Money Itinerary Offer Coverage, Coverage and terminal statuses, 04 — Data, Persistence, and REST API Contracts, Normative versioned REST design, Normative versioned REST v1 and canonical DTOs (+14 more)

### Community 36 - "Provider Feasibility Docs"
Cohesion: 0.10
Nodes (20): Exact decimal money and FX provenance, 03 — Provider Feasibility, Multi-Provider Aggregation, and Fare Accuracy, Normalized provider error taxonomy, Itinerary versus seller offer, Conservative itinerary identity and separate fare offers, Comparable exact money, Typed provider failures versus successful empty, Provider feasibility and permission gate (+12 more)

### Community 37 - "05 — Web + Native iOS Client Implementation"
Cohesion: 0.29
Nodes (7): 05 — Web + Native iOS Client Implementation, Polling and recovery design, Web first iOS second, Native SwiftUI implementation plan, Web and SwiftUI share remote search engine, P5 native iOS gate, Native SwiftUI P5

### Community 38 - "Bounded Calls"
Cohesion: 0.08
Nodes (19): BoundedCall, __init__(), test_bounded_swoop_executor_c3_has_actual_overlap_and_no_queue(), __init__(), __init__(), __init__(), 2. Implementation, 3. Configuration review (+11 more)

### Community 40 - "P4.11 Fli Log"
Cohesion: 0.11
Nodes (19): Historical usable quote verification, P4.11 — Fli as a fourth provider, Truthful failure and cache semantics, Fourth provider Fli public Google Flights page, P4.11 acceptance evidence, Explicit HTTP2 transport, Indicative Google quotes and generic search links, Historical HTTP2 live measurements (+11 more)

### Community 41 - "results_projection"
Cohesion: 0.15
Nodes (21): capabilities(), create_search(), AirportTransfer, Capabilities, Coverage, Created, DTO, ExpiredObservation (+13 more)

### Community 42 - "p48_intervals.py"
Cohesion: 0.14
Nodes (7): Measurements, ObservedProvider, observers(), make_send(), observed(), post(), utc()

### Community 43 - "Skiplagged Probe"
Cohesion: 0.15
Nodes (9): main(), main(), main(), run(), _utc_now_iso(), main(), run(), _to_jsonable() (+1 more)

### Community 44 - "Client Errors"
Cohesion: 0.22
Nodes (11): ApiError, BASE_URL, request(), TERMINAL_STATUSES, errorMessage(), getOwnerToken(), setOwnerToken(), Capabilities (+3 more)

### Community 45 - "Route Expansion"
Cohesion: 0.42
Nodes (7): expand_routes_and_dates(), RouteDateCombo, _query(), test_1x3x9_expands_to_27_combinations(), test_combos_are_unique_and_deterministic_order(), test_duplicate_input_codes_are_deduplicated_before_expansion(), test_same_origin_destination_pair_is_skipped()

### Community 46 - "Product Requirements"
Cohesion: 0.22
Nodes (10): Accessible responsive UI, 01 — Product Requirements, Rules, and UX Acceptance, One-way adult economy flight finder, Flexible one-way finder scope, Query coverage differs from inventory completeness, Conservative fare ranking, Safe Best checked and Lowest advertised views, Honest results states (+2 more)

### Community 47 - "P46 Browser Tests"
Cohesion: 0.28
Nodes (6): all, dist, job, offer(), richEntries, trip()

### Community 48 - "Registration"
Cohesion: 0.14
Nodes (31): JobRunner, FakeProvider, Registration, test_api_scheduler_results_contract(), test_baggage_eligibility_and_snapshot_cursor(), test_capabilities_report_default_source_selection(), test_pagination_freezes_incremental_quote_set(), payload() (+23 more)

### Community 49 - "Offer"
Cohesion: 0.12
Nodes (22): SourceEvidence, ItinerarySummary, FXSnapshot, Offer, ProviderSearchResult, aware_iso(), decimal_value(), money() (+14 more)

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

### Community 55 - "datetime"
Cohesion: 0.11
Nodes (9): CoverageEntry, unique_covered_combinations(), WorkStatus, ScriptedOutcome, _entry(), test_failed_terminal_requires_error_code(), test_failure_is_not_counted_as_covered(), test_succeeded_empty_cannot_carry_error_code() (+1 more)

### Community 56 - "batch"
Cohesion: 0.13
Nodes (10): live_guard(), batch(), emit(), main(), provider_run(), migrated(), peak(), percentile() (+2 more)

### Community 57 - "Icon Sprite"
Cohesion: 0.67
Nodes (3): Bluesky, Discord, GitHub and X logos, Reusable SVG icon sprite, Purple documentation and social profile icons

### Community 75 - "CheapWings P4.8 — Throughput, Concurrency & Reliability Experiment"
Cohesion: 0.12
Nodes (16): Alternative architecture assessment, Authorization and method, CheapWings P4.8 — Throughput, Concurrency & Reliability Experiment, Experiment A — completed live results, Experiment B — offline Python scheduler stress, Experiment C — offline overlapping failure injection, Follow-up — requested C3/1s trials and swoop retry (2026-11-11 Jakarta), Follow-up sanitized per-search ledger (+8 more)

### Community 76 - "Provider feasibility evidence"
Cohesion: 0.13
Nodes (15): Claims vs observed, Claims vs observed, Combined P0 gate outcome, Fields present / absent (for canonical domain mapping), Follow-up probe items, Legal/compliance note (the real risk for swoop), Live sample (redacted selector/links kept short; full in fixture), Owner decisions (resolved 2026-11-09, per `docs/06` stop/escalation rule) (+7 more)

### Community 77 - "p412_pool_benchmark.py"
Cohesion: 0.14
Nodes (8): main(), peak(), quantile(), query(), scenario(), summarize(), threads(), main()

### Community 78 - "test_p48_failures.py"
Cohesion: 0.20
Nodes (17): FareQuote, reg(), drain(), record(), short(), test_actual_worker_process_kill_and_recovery(), recover(), test_concurrent_claims_under_real_sqlite_lock() (+9 more)

### Community 79 - "SingleDateRouteQuery"
Cohesion: 0.08
Nodes (19): SearchProvider, SingleDateRouteQuery, json_payload(), OctotripProvider, HttpStartGate, offer_from_row(), test_octotrip_429_stops_unsent_peer_http(), test_octotrip_gate_covers_initialization_across_three_sessions() (+11 more)

### Community 80 - "P4.5 UI/UX handover, intake and fixes"
Cohesion: 0.14
Nodes (17): P2–P4 implementation log, Historical CGK to CTS cancelled review, P2 recorded acceptance, P3 adapter normalization and acceptance, P4 React implementation, P4 typed client and polling reliability, Polling effects and stale-page fencing, Historical review follow-ups (+9 more)

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

### Community 87 - "test_locations.py"
Cohesion: 0.30
Nodes (10): resolve_location(), catalog(), selection(), test_ambiguous_cities_keep_distinct_ids_and_geography(), test_boundary_and_overlap_match_expansion(), test_catalog_rejects_inconsistent_data(), test_lookup(), test_major_resolution_and_no_fallback() (+2 more)

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

### Community 105 - "query.py"
Cohesion: 0.22
Nodes (3): MaxStops, plan_scope(), test_zero_routes_and_date_changes()

## Knowledge Gaps
- **78 isolated node(s):** `cheapwings`, `API application domain dependency boundaries`, `Snapshot cursor pagination and ranked quote`, `Owner access and request admission`, `Capability-driven provider abstraction` (+73 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 599 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CheapWings — Worker Implementation Handoff` connect `WORK_LOG.md — Current State (keep under ~80 lines)` to `REST Contracts Docs`, `Provider Feasibility Docs`, `05 — Web + Native iOS Client Implementation`, `02 — System Architecture and Runtime Boundaries`, `Product Requirements`, `P4.5 UI/UX handover, intake and fixes`, `Architecture Docs`, `FlightFinder — Architecture & Design Review Handoff`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Are the 87 inferred relationships involving `Repository` (e.g. with `AirportTransfer` and `IdentityConfidence`) actually correct?**
  _`Repository` has 87 INFERRED edges - model-reasoned connections that need verification._
- **What connects `cheapwings`, `API application domain dependency boundaries`, `Snapshot cursor pagination and ranked quote` to the rest of the system?**
  _78 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Repository` be split into smaller, more focused modules?**
  _Cohesion score 0.1320921985815603 - nodes in this community are weakly interconnected._
- **Why does `FlightFinder — Architecture & Design Review Handoff` connect `FlightFinder — Architecture & Design Review Handoff` to `11. Minimal Test Plan and Evaluation Matrix`, `20. Mandatory Cross-Platform and Multi-Provider Acceptance Tests`, `4. Architecture Proposal`, `7. Price Verification Policy`, `8. Filtering and Travel Risks`, `19. Python Tech Stack Decision, Long-Running Jobs, and Cross-Platform Integration`, `17. Mandatory Multi-Provider Aggregation Architecture (restored; mandatory)`, `12. MVP Milestones and Checkpoints`, `18. Web + Native iOS Product Design`, `1. Product Intent, Requirements, and Non-Goals`, `2. Proposed Search Experience / UX`, `3. Candidate Data Sources and Due-Diligence Notes`, `15. Mandatory Deliverables from the Reviewing Agent`, `5. Search Algorithm, Coverage, and Failure Handling`, `6. Fare Data Model & Comparability`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Are the 39 inferred relationships involving `ProviderFailure` (e.g. with `ExactCapture` and `FliProvider`) actually correct?**
  _`ProviderFailure` has 39 INFERRED edges - model-reasoned connections that need verification._
- **Should `swoop.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1396011396011396 - nodes in this community are weakly interconnected._