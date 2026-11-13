# Graph Report - p5.05-native-ios-analysis  (2026-11-13)

## Corpus Check
- 224 files · ~310,391 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 25 file(s) not represented in the graph (top: (none) 12, .jsonl 5, .css 3)

## Summary
- 2080 nodes · 5770 edges · 143 communities (108 shown, 35 thin omitted)
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 1226 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `77c99cf4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- .create_job
- .run
- Money
- test_octotrip.py
- test_p49_review.py
- swoop.py
- base
- sqlalchemy
- P46ResultsWorkspace.tsx
- rust/src/lib.rs
- test_fli.py
- search_service.py
- App.tsx
- StatusVisuals.tsx
- 06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria
- test_money.py
- CheapWings
- catalog.py
- test_api.py
- WORK_LOG.md — Current State (keep under ~80 lines)
- Provider and result-cache research (2026-11-10)
- Experiment
- SwoopProvider
- types.ts
- SearchForm.tsx
- FlightSegment
- pytest
- common
- package.json
- compilerOptions
- P5.05 — Native iOS search engine feasibility analysis
- test_search_cache.py
- p412-browser.mjs
- compilerOptions
- P4.10 — Smart location selection
- 06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria
- 03 — Provider Feasibility, Multi-Provider Aggregation, and Fare Accuracy
- Repository
- BoundedCall
- datetime
- P4.11 — Fli as a fourth provider
- contracts.py
- p48_intervals.py
- pathlib
- ProbeResult
- expand_routes_and_dates
- 01 — Product Requirements, Rules, and UX Acceptance
- p46-browser.mjs
- Outcome
- JobRunner
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
- p49_scheduler_comparison.py
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
- repository.py
- Registration
- build_location_catalog.py
- Tfs
- pytest
- ProbeView
- p412_report.py
- Fli probe — P5.06 spikes S1 (iPhone) and S3 (Swift off-device)
- PackageDescription
- UserAgentMode
- parity.py
- SwiftCore
- build.sh
- fli-wreq
- cheapwings-money-rs
- cheapwings-money-rs
- cache.py
- S5View.swift
- test_overlap_429_retry_after_and_independent_provider
- FakeProvider
- 02 — System Architecture and Runtime Boundaries
- P4.12 — Shared global resource pool
- gen_fixtures.py
- Foundation
- test_p48_scheduler_review.py
- Pre-restructure WORK_LOG header (baseline, full tracker, ledger, summary, deviations)
- .search
- rust/build.sh
- test_recorded_real_adapters_api_summary_fx_and_expiry
- core-s5

## God Nodes (most connected - your core abstractions)
1. `Repository` - 113 edges
2. `ProviderFailure` - 99 edges
3. `FakeProvider` - 94 edges
4. `Registration` - 94 edges
5. `JobRunner` - 66 edges
6. `SearchQuery` - 48 edges
7. `now_ms()` - 42 edges
8. `Offer` - 41 edges
9. `results_projection()` - 40 edges
10. `SingleDateRouteQuery` - 38 edges

## Surprising Connections (you probably didn't know these)
- `19.4 Typed provider contract and canonical behavior` --references--> `SingleDateRouteQuery`  [INFERRED]
  docs/reference/V4_FULL_DESIGN_REFERENCE.md → backend/src/cheapwings/providers/base.py
- `3. Native engine design and module ownership` --references--> `Money`  [INFERRED]
  docs/log/p5.05.md → backend/src/cheapwings/domain/money.py
- `17.2 Separate itinerary from offer` --references--> `Itinerary`  [INFERRED]
  docs/reference/V4_FULL_DESIGN_REFERENCE.md → backend/src/cheapwings/domain/itinerary.py
- `2. Implementation` --references--> `BoundedCall`  [INFERRED]
  docs/log/p4.12.md → backend/src/cheapwings/providers/swoop.py
- `4. Port-vs-drop matrix` --references--> `ResultsExpired`  [INFERRED]
  docs/log/p5.05.md → backend/src/cheapwings/storage/verification.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Planned SwiftUI shares backend contract and durable recovery** — docs_05_web_and_native_ios_swiftui_plan, docs_06_implementation_checkpoints_p5, readme_ios_planned [EXTRACTED 1.00]
- **Exact identity, exact money and unknown-safe rankings** — docs_03_providers_aggregation_pricing_itinerary_offer_identity, docs_03_providers_aggregation_pricing_decimal_money_fx, docs_01_product_requirements_ux_safe_and_advertised_rankings, docs_04_data_and_api_contracts_three_valued_unknowns [INFERRED 0.85]
- **Canonical fare evidence remains conservative across adapters and clients** — docs_03_providers_aggregation_pricing_money, docs_04_data_and_api_contracts_three_valued, docs_log_p4_11_fare_limits, readme_safe_ranking [INFERRED 0.95]

## Communities (143 total, 35 thin omitted)

### Community 0 - ".create_job"
Cohesion: 0.16
Nodes (26): Logged, test_blocking_adapter_pool_sized_to_g_uses_real_threads(), test_cooled_provider_stops_starting_and_others_take_the_pool(), search(), test_headroom_lets_late_higher_priority_work_start_immediately(), test_headroom_unused_without_an_available_higher_priority_source(), test_lower_priority_only_gets_slots_higher_tiers_cannot_use(), test_paced_provider_overlaps_with_actual_start_gaps() (+18 more)

### Community 1 - ".run"
Cohesion: 0.13
Nodes (8): Decoded, DecodeError, .description, partialPayload, schemaChanged, Leg, Offer, Page

### Community 3 - "test_octotrip.py"
Cohesion: 0.13
Nodes (15): json_payload(), OctotripProvider, test_octotrip_429_stops_unsent_peer_http(), test_octotrip_gate_covers_initialization_across_three_sessions(), respond(), payload(), query(), test_bad_source_values_fail_or_disable_navigation() (+7 more)

### Community 4 - "test_p49_review.py"
Cohesion: 0.14
Nodes (18): MeasuredProduction, ReviewDispatcher, ReviewRepository, TimedFake, drain(), max_overlap(), query(), test_cooldown_occupies_no_execution_slot() (+10 more)

### Community 5 - "swoop.py"
Cohesion: 0.10
Nodes (17): airport_transfers(), AirportTransfer, ItinerarySummary, Offer, ProviderCapabilities, ProviderRepriceResult, ProviderSearchResult, SearchProvider (+9 more)

### Community 6 - "base"
Cohesion: 0.06
Nodes (34): CODE_SIGN_STYLE, CURRENT_PROJECT_VERSION, GENERATE_INFOPLIST_FILE, INFOPLIST_KEY_UILaunchScreen_Generation, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPad, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPhone, MARKETING_VERSION, PRODUCT_BUNDLE_IDENTIFIER (+26 more)

### Community 7 - "sqlalchemy"
Cohesion: 0.12
Nodes (7): upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade()

### Community 8 - "P46ResultsWorkspace.tsx"
Cohesion: 0.13
Nodes (29): PriceStatus, PublicItinerary, PublicOffer, FareRiskNotice(), formatDuration(), ItineraryCard(), BAG_LABEL, COMPARISON_LABEL (+21 more)

### Community 9 - "rust/src/lib.rs"
Cohesion: 0.06
Nodes (37): as_minor_units(), best_checked_deal(), exponent(), EXPONENTS, fingerprint(), FingerprintCase, Fixtures, from_minor_units() (+29 more)

### Community 10 - "test_fli.py"
Cohesion: 0.19
Nodes (14): decoder(), payload(), provider(), query(), test_c3_real_threads_overlap_and_cancel_retains_physical_capacity(), fetch(), test_challenge_redirect_is_not_followed(), test_exact_prices_identity_and_conservative_evidence() (+6 more)

### Community 11 - "search_service.py"
Cohesion: 0.08
Nodes (16): create_app(), cancel(), get_job(), get_results(), health(), resolve_location(), _exact_reprice_count(), instant() (+8 more)

### Community 12 - "App.tsx"
Cohesion: 0.13
Nodes (23): api, ApiError, BASE_URL, request(), TERMINAL_STATUSES, errorMessage(), getOwnerToken(), setOwnerToken() (+15 more)

### Community 13 - "StatusVisuals.tsx"
Cohesion: 0.27
Nodes (10): ProviderProgress, WorkerPool, LABEL, P46SearchProgress(), PoolGauge(), ProviderBars(), SEGMENTS, SOURCE_NAMES (+2 more)

### Community 14 - "06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria"
Cohesion: 0.12
Nodes (16): Provider feasibility and permission gate, 05 — Web + Native iOS Client Implementation, Polling and recovery design, Web first iOS second, Native SwiftUI implementation plan, Web and SwiftUI share remote search engine, 06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria, Fundamental incompatibility escalation (+8 more)

### Community 15 - "test_money.py"
Cohesion: 0.21
Nodes (7): minor_unit_exponent(), UnknownCurrencyError, test_cannot_compare_different_currencies(), test_idr_has_zero_minor_units(), test_money_rejects_float(), test_money_requires_known_currency_for_minor_units(), test_usd_has_two_minor_units()

### Community 16 - "CheapWings"
Cohesion: 0.13
Nodes (22): Synthetic browser regressions, CheapWings web, React TypeScript Vite thin client, Runtime private access, Memory-only web owner token, Intercepted Playwright browser regression suite, React Vite thin client, Fare evidence tiers (+14 more)

### Community 17 - "catalog.py"
Cohesion: 0.20
Nodes (4): fold(), LocationCatalog, MajorResolution, MajorSelection

### Community 18 - "test_api.py"
Cohesion: 0.11
Nodes (30): Settings, default_registry(), require_current_schema(), main(), worker_lock(), client_for(), request_data(), test_auth_and_remote_boundary() (+22 more)

### Community 19 - "WORK_LOG.md — Current State (keep under ~80 lines)"
Cohesion: 0.09
Nodes (24): Authorized task boundaries, Preserve current baseline, 08 — Starting Prompt for a Local Coding Agent, Implementation invariants, Single reporting location, Evidence and phase-history index, Dated history is evidence rather than active instructions, 2026-11-11 documentation cleanup (+16 more)

### Community 20 - "Provider and result-cache research (2026-11-10)"
Cohesion: 0.07
Nodes (30): Cache and OctoTrip implementation kickoff (2026-11-10), Dated provider evaluation — primary sources, not production approval, Final live acceptance and handover — cache + OctoTrip, Hosted endpoint preflight — actual observations and limits, Implementation checkpoint — durable cache and backend selection (in progress), Live owner search — cross-provider overlap confirmed (2026-11-10), Offline cache/OctoTrip acceptance checkpoint, Owner approval — publish and merge cache/OctoTrip integration (2026-11-10) (+22 more)

### Community 21 - "Experiment"
Cohesion: 0.12
Nodes (8): Experiment, post(), wrap(), observed(), test_octotrip_three_sessions_share_one_http_gate(), session(), test_response_timing_preserves_stream_bytes(), respond()

### Community 22 - "SwoopProvider"
Cohesion: 0.17
Nodes (15): SourceEvidence, FXSnapshot, SkiplaggedProvider, SwoopProvider, load(), query(), test_dst_ambiguity_rejected(), test_missing_zone_retains_unmatched_summary() (+7 more)

### Community 23 - "types.ts"
Cohesion: 0.10
Nodes (17): AirportTransfer, ComparisonStatus, Coverage, ExpiredObservation, IdentityConfidence, Job, JobPhase, JobStatus (+9 more)

### Community 24 - "SearchForm.tsx"
Cohesion: 0.17
Nodes (17): Currency, ProviderCapability, SearchRequest, AirportMultiSelect(), Props, Props, SearchForm(), todayIso() (+9 more)

### Community 25 - "FlightSegment"
Cohesion: 0.09
Nodes (25): run_demo(), compute_fingerprint(), IdentityConfidence, Itinerary, FlightSegment, build_itinerary(), ItineraryGroup, MatchEngine (+17 more)

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
Cohesion: 0.20
Nodes (10): 10. Sources, facts and open questions, 1. Executive verdict, 2. Provider compatibility matrix, 3. Native engine design and module ownership, 5. Background / foreground behaviour (iOS), 6. Risk register (likelihood × impact, 1–5), 7. Experiment plan (proposal; nothing run; each needs owner approval), 8. Architecture decision record (+2 more)

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

### Community 35 - "06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria"
Cohesion: 0.12
Nodes (16): Scheduler design requirements, Authentication and secret boundary, Canonical Money Itinerary Offer Coverage, Coverage and terminal statuses, 04 — Data, Persistence, and REST API Contracts, Normative versioned REST design, Normative versioned REST v1 and canonical DTOs, SQLite persistence schema direction (+8 more)

### Community 36 - "03 — Provider Feasibility, Multi-Provider Aggregation, and Fare Accuracy"
Cohesion: 0.13
Nodes (16): Exact decimal money and FX provenance, 03 — Provider Feasibility, Multi-Provider Aggregation, and Fare Accuracy, Normalized provider error taxonomy, Itinerary versus seller offer, Conservative itinerary identity and separate fare offers, Comparable exact money, Typed provider failures versus successful empty, P0 provider feasibility gate (+8 more)

### Community 37 - "Repository"
Cohesion: 0.18
Nodes (18): write_session(), now_ms(), Repository, test_reprice_job_is_not_starved_by_shared_search_backlog(), test_configured_query_cap_survives_snapshot(), test_migrations_constraints_and_snapshot(), test_atomic_claim_and_global_limit(), test_cancel_fences_late_response_preserves_success() (+10 more)

### Community 38 - "BoundedCall"
Cohesion: 0.08
Nodes (18): HttpStartGate, BoundedCall, __init__(), test_bounded_swoop_executor_c3_has_actual_overlap_and_no_queue(), __init__(), __init__(), __init__(), _query() (+10 more)

### Community 39 - "datetime"
Cohesion: 0.12
Nodes (5): DispatchDeferred, main(), live_guard(), main(), trial()

### Community 40 - "P4.11 — Fli as a fourth provider"
Cohesion: 0.11
Nodes (19): Historical usable quote verification, P4.11 — Fli as a fourth provider, Truthful failure and cache semantics, Fourth provider Fli public Google Flights page, P4.11 acceptance evidence, Explicit HTTP2 transport, Indicative Google quotes and generic search links, Historical HTTP2 live measurements (+11 more)

### Community 41 - "contracts.py"
Cohesion: 0.16
Nodes (18): capabilities(), worker_pool(), AirportTransfer, Capabilities, Coverage, Created, DTO, ExpiredObservation (+10 more)

### Community 42 - "p48_intervals.py"
Cohesion: 0.13
Nodes (9): Measurements, ObservedProvider, observers(), make_send(), observed(), post(), run(), utc() (+1 more)

### Community 43 - "pathlib"
Cohesion: 0.16
Nodes (10): append_result(), main(), main(), main(), run(), _utc_now_iso(), main(), run() (+2 more)

### Community 44 - "ProbeResult"
Cohesion: 0.32
Nodes (4): FliProbe, isAllowedRedirect(), ProbeResult, .summary

### Community 45 - "expand_routes_and_dates"
Cohesion: 0.42
Nodes (7): expand_routes_and_dates(), RouteDateCombo, _query(), test_1x3x9_expands_to_27_combinations(), test_combos_are_unique_and_deterministic_order(), test_duplicate_input_codes_are_deduplicated_before_expansion(), test_same_origin_destination_pair_is_skipped()

### Community 46 - "01 — Product Requirements, Rules, and UX Acceptance"
Cohesion: 0.22
Nodes (10): Accessible responsive UI, 01 — Product Requirements, Rules, and UX Acceptance, One-way adult economy flight finder, Flexible one-way finder scope, Query coverage differs from inventory completeness, Conservative fare ranking, Safe Best checked and Lowest advertised views, Honest results states (+2 more)

### Community 47 - "p46-browser.mjs"
Cohesion: 0.28
Nodes (6): all, dist, job, offer(), richEntries, trip()

### Community 48 - "Outcome"
Cohesion: 0.17
Nodes (12): Outcome, blockedRedirect, blockedSorry, blockedTraffic, crossCheckFailed, httpError, .mustStop, networkError (+4 more)

### Community 49 - "JobRunner"
Cohesion: 0.15
Nodes (15): DispatchFailure, JobRunner, test_fli_real_normalization_api_prices_and_cache(), transport(), test_fli_uses_durable_shared_fetch_cancel_fencing_and_cache(), test_missing_fli_payload_is_failure_and_never_cached(), test_short_source_expiry_preserves_other_source_and_running_job(), test_dispatch_database_failure_surfaces() (+7 more)

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
Cohesion: 0.24
Nodes (8): CoverageEntry, unique_covered_combinations(), WorkStatus, _entry(), test_failed_terminal_requires_error_code(), test_failure_is_not_counted_as_covered(), test_succeeded_empty_cannot_carry_error_code(), test_unique_covered_combinations_does_not_double_count_providers()

### Community 56 - "p48_throughput.py"
Cohesion: 0.14
Nodes (10): live_guard(), batch(), emit(), main(), provider_run(), migrated(), peak(), percentile() (+2 more)

### Community 57 - "Reusable SVG icon sprite"
Cohesion: 0.67
Nodes (3): Bluesky, Discord, GitHub and X logos, Reusable SVG icon sprite, Purple documentation and social profile icons

### Community 60 - "search_service.py"
Cohesion: 0.12
Nodes (25): PublicOffer, shortlist(), ComparisonStatus, LinkScope, PriceStatus, ProviderErrorCode, ThreeValued, best_checked_deal() (+17 more)

### Community 75 - "CheapWings P4.8 — Throughput, Concurrency & Reliability Experiment"
Cohesion: 0.12
Nodes (16): Alternative architecture assessment, Authorization and method, CheapWings P4.8 — Throughput, Concurrency & Reliability Experiment, Experiment A — completed live results, Experiment B — offline Python scheduler stress, Experiment C — offline overlapping failure injection, Follow-up — requested C3/1s trials and swoop retry (2026-11-11 Jakarta), Follow-up sanitized per-search ledger (+8 more)

### Community 76 - "provider-feasibility-evidence.md"
Cohesion: 0.12
Nodes (15): Claims vs observed, Claims vs observed, Combined P0 gate outcome, Fields present / absent (for canonical domain mapping), Follow-up probe items, Legal/compliance note (the real risk for swoop), Live sample (redacted selector/links kept short; full in fixture), Owner decisions (resolved 2026-11-09, per `docs/06` stop/escalation rule) (+7 more)

### Community 77 - "p412_pool_benchmark.py"
Cohesion: 0.24
Nodes (9): main(), migrated(), peak(), quantile(), query(), scenario(), summarize(), threads() (+1 more)

### Community 78 - "p49_scheduler_comparison.py"
Cohesion: 0.16
Nodes (8): database(), migrated(), quantile(), replay_latencies(), run_trial(), admit(), Scenario, scenarios()

### Community 79 - "ProviderFailure"
Cohesion: 0.08
Nodes (17): ProviderFailure, exact_http_client(), observe(), ExactCapture, FliProvider, provider_failure(), retry_after(), mcp_search() (+9 more)

### Community 80 - "P4.5 UI/UX handover, intake and fixes"
Cohesion: 0.13
Nodes (18): P2–P4 implementation log, Historical CGK to CTS cancelled review, P2 recorded acceptance, P3 adapter normalization and acceptance, P3 evidence-preserving provider adapters, P4 React implementation, P4 typed client and polling reliability, Polling effects and stale-page fencing (+10 more)

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
Cohesion: 0.19
Nodes (12): plan_scope(), catalog(), selection(), test_ambiguous_cities_keep_distinct_ids_and_geography(), test_boundary_and_overlap_match_expansion(), test_catalog_rejects_inconsistent_data(), test_lookup(), test_major_resolution_and_no_fallback() (+4 more)

### Community 88 - "test_p48_failures.py"
Cohesion: 0.11
Nodes (6): lifespan(), fixture(), engine(), migrate(), query(), main()

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

### Community 105 - "MaxStops"
Cohesion: 0.40
Nodes (3): create_search(), SearchRequest, MaxStops

### Community 107 - "shadow_money.py"
Cohesion: 0.25
Nodes (6): pytest_configure(), as_minor_units(), convert(), from_minor_units(), minor_unit_exponent(), _shadow()

### Community 108 - "repository.py"
Cohesion: 0.18
Nodes (15): Base, FareQuote, FXRow, ItineraryRow, ProviderState, QuoteRevision, SearchJob, SegmentRow (+7 more)

### Community 109 - "Registration"
Cohesion: 0.14
Nodes (20): ScriptedOutcome, Registration, test_api_scheduler_results_contract(), test_pagination_freezes_incremental_quote_set(), payload(), test_airport_change_never_claims_ground_cost_is_known_on_reprice(), reprice(), search() (+12 more)

### Community 112 - "pytest"
Cohesion: 0.49
Nodes (8): _base(), test_include_hidden_city_defaults_false_and_does_not_silently_flip(), test_rejects_excessive_combination_count(), test_rejects_invalid_iata(), test_rejects_multi_adult_in_mvp(), test_rejects_reversed_dates(), test_rejects_roundtrip_in_mvp(), test_rejects_same_origin_and_destination()

### Community 113 - "ProbeView"
Cohesion: 0.14
Nodes (7): WreqProbe, FliProbeApp, .body, ProbeView, .body, S5Section, .body

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

### Community 119 - "SwiftCore"
Cohesion: 0.21
Nodes (8): FingerprintCase, Fixtures, Instant, MoneyCase, Offer, RankingCase, Segment, SwiftCore

### Community 120 - "build.sh"
Cohesion: 0.33
Nodes (5): DEVELOPER_DIR, IPHONEOS_DEPLOYMENT_TARGET, MACOSX_DEPLOYMENT_TARGET, PATH, build.sh script

### Community 127 - "cache.py"
Cohesion: 0.19
Nodes (5): cache_key(), CacheRepository, without_handles(), OperationAttempt, ProviderOperation

### Community 128 - "S5View.swift"
Cohesion: 0.14
Nodes (9): RustCore, SizeApp, .body, SizeApp, .body, SizeApp, .body, SwiftCore (+1 more)

### Community 129 - "test_overlap_429_retry_after_and_independent_provider"
Cohesion: 0.21
Nodes (14): reg(), drain(), record(), short(), test_concurrent_claims_under_real_sqlite_lock(), claim(), test_overlap_429_retry_after_and_independent_provider(), search() (+6 more)

### Community 130 - "FakeProvider"
Cohesion: 0.21
Nodes (10): SingleDateRouteQuery, FakeProvider, test_safe_external_link_policy(), sample(), test_cancel_does_not_release_live_global_slot(), search(), test_offer_write_rollback_is_atomic(), test_three_provider_requests_overlap_without_extra_task_pools() (+2 more)

### Community 131 - "02 — System Architecture and Runtime Boundaries"
Cohesion: 0.18
Nodes (11): Bounded blocking provider execution, API application domain dependency boundaries, Dependency boundary, 02 — System Architecture and Runtime Boundaries, Durable job and work state, Capability-driven provider abstraction, Provider capability protocols, P2 durable storage and REST implementation (+3 more)

### Community 132 - "P4.12 — Shared global resource pool"
Cohesion: 0.15
Nodes (12): 2. Implementation, 3. Configuration review, 4. Regression tests, 6. Risk analysis, 7. Recommended production configuration, 8. Owner decisions, Conservative live Fli ladder (owner-approved), Follow-up — priority tiers and low-priority headroom (2026-11-12) (+4 more)

### Community 133 - "gen_fixtures.py"
Cohesion: 0.21
Nodes (6): fingerprint_cases(), instant(), money_cases(), offer(), outcome(), ranking_cases()

### Community 134 - "Foundation"
Cohesion: 0.18
Nodes (5): CryptoKit, FliProbe, FliWreq, Foundation, SelfTest

### Community 135 - "test_p48_scheduler_review.py"
Cohesion: 0.33
Nodes (6): fetch(), result(), scope(), test_restart_preserves_spacing_and_provider_cooldown(), test_restart_waits_for_lease_and_fences_duplicate_claims(), test_unequal_intervals_short_and_long_calls()

### Community 136 - "Pre-restructure WORK_LOG header (baseline, full tracker, ledger, summary, deviations)"
Cohesion: 0.22
Nodes (9): Canonical evidence-preserving extensions, Pre-restructure WORK_LOG header (baseline, full tracker, ledger, summary, deviations), 2026-11-09 empty-repo baseline, Historical initial repository and toolchain, Pre-restructure phase summary, FlightFinder renamed CheapWings, Owner acceptance and merge4c98386, Dated evidence index (+1 more)

### Community 137 - ".search"
Cohesion: 0.29
Nodes (5): search(), search(), search(), search(), search()

### Community 138 - "rust/build.sh"
Cohesion: 0.33
Nodes (5): DEVELOPER_DIR, IPHONEOS_DEPLOYMENT_TARGET, MACOSX_DEPLOYMENT_TARGET, PATH, build.sh script

## Knowledge Gaps
- **119 isolated node(s):** `core-s5`, `PATH`, `DEVELOPER_DIR`, `IPHONEOS_DEPLOYMENT_TARGET`, `MACOSX_DEPLOYMENT_TARGET` (+114 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 757 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **35 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `P4.12 — Shared global resource pool` connect `P4.12 — Shared global resource pool` to `StatusVisuals.tsx`, `Repository`, `BoundedCall`?**
  _High betweenness centrality (0.165) - this node is a cross-community bridge._
- **Are the 88 inferred relationships involving `Repository` (e.g. with `AirportTransfer` and `IdentityConfidence`) actually correct?**
  _`Repository` has 88 INFERRED edges - model-reasoned connections that need verification._
- **What connects `core-s5`, `PATH`, `DEVELOPER_DIR` to the rest of the system?**
  _119 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `.run` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._
- **Why does `Search-status visualization (2026-11-12)` connect `StatusVisuals.tsx` to `P4.12 — Shared global resource pool`?**
  _High betweenness centrality (0.161) - this node is a cross-community bridge._
- **Are the 41 inferred relationships involving `ProviderFailure` (e.g. with `JobRunner` and `ExactCapture`) actually correct?**
  _`ProviderFailure` has 41 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_octotrip.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1349206349206349 - nodes in this community are weakly interconnected._