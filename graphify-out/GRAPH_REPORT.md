# Graph Report - CheapWings  (2026-11-12)

## Corpus Check
- 211 files · ~281,038 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: (none) 3, .css 3, .example 2)

## Summary
- 1412 nodes · 4584 edges · 75 communities (56 shown, 19 thin omitted)
- Extraction: 76% EXTRACTED · 24% INFERRED · 0% AMBIGUOUS · INFERRED: 1094 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Job Runner
- Coverage Ledger
- Money and FX
- Provider Failures
- Measured Production
- Search Service and Demo
- Stdlib Imports
- Octotrip Provider
- Itinerary UI
- Settings and Env
- Fli Provider
- Runner Dependencies
- Web API Client
- Query and Cache
- API Routes
- Skiplagged and Swoop
- Architecture Docs
- Location Catalog
- API Tests
- Work Log
- Provider Contracts
- Throughput Experiment
- Alembic Migrations
- Web Types
- Search Form
- Itinerary Domain
- Search Query Model
- Agent Prompt Docs
- Web Dev Deps
- tsconfig App
- Shortlist Verification
- Reprice Contracts
- Browser Test Tooling
- tsconfig Node
- P4.10 Locations Log
- REST Contracts Docs
- Provider Feasibility Docs
- iOS Client Docs
- Bounded Calls
- Itinerary Tests
- P4.11 Fli Log
- Cache Repository
- Observed Provider
- Skiplagged Probe
- Client Errors
- Route Expansion
- Product Requirements
- P46 Browser Tests
- Dispatch Failures
- Web Client Docs
- Catalog Build Script
- Package Scripts
- Location Licenses
- Lint Config
- Browser Fixtures
- Coverage Tests
- Request DTO
- Icon Sprite
- Vite Env Types
- tsconfig Root
- Dispatch Deferred
- Web Entry HTML
- Favicon
- React Logo
- Package Init 65
- Package Init 74

## God Nodes (most connected - your core abstractions)
1. `Repository` - 102 edges
2. `ProviderFailure` - 95 edges
3. `FakeProvider` - 89 edges
4. `Registration` - 83 edges
5. `JobRunner` - 57 edges
6. `SearchQuery` - 43 edges
7. `results_projection()` - 40 edges
8. `Offer` - 40 edges
9. `now_ms()` - 38 edges
10. `WorkStatus` - 36 edges

## Surprising Connections (you probably didn't know these)
- `Runtime private access` --semantically_similar_to--> `Memory-only web bearer`  [INFERRED] [semantically similar]
  apps/web/README.md → README.md
- `MIT airport data license` --semantically_similar_to--> `MIT airport data license`  [INFERRED] [semantically similar]
  apps/web/public/locations-LICENSE.txt → backend/src/cheapwings/locations/LICENSE.txt
- `run()` --uses--> `JobRunner`  [INFERRED]
  scripts/benchmarks/p48_intervals.py → backend/src/cheapwings/application/job_runner.py
- `batch()` --uses--> `JobRunner`  [INFERRED]
  scripts/benchmarks/p48_throughput.py → backend/src/cheapwings/application/job_runner.py
- `run()` --uses--> `Settings`  [INFERRED]
  scripts/benchmarks/p48_intervals.py → backend/src/cheapwings/config.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Exact identity, exact money and unknown-safe rankings** — docs_03_providers_aggregation_pricing_itinerary_offer_identity, docs_03_providers_aggregation_pricing_decimal_money_fx, docs_01_product_requirements_ux_safe_and_advertised_rankings, docs_04_data_and_api_contracts_three_valued_unknowns [INFERRED 0.85]
- **Canonical fare evidence remains conservative across adapters and clients** — docs_03_providers_aggregation_pricing_money, docs_04_data_and_api_contracts_three_valued, docs_log_p4_11_fare_limits, readme_safe_ranking [INFERRED 0.95]
- **Planned SwiftUI shares backend contract and durable recovery** — docs_05_web_and_native_ios_swiftui_plan, docs_06_implementation_checkpoints_p5, readme_ios_planned [EXTRACTED 1.00]

## Communities (75 total, 19 thin omitted)

### Community 0 - "Job Runner"
Cohesion: 0.06
Nodes (113): JobRunner, FakeProvider, Registration, write_session(), FareQuote, ProviderResultCache, ProviderState, WorkAttempt (+105 more)

### Community 1 - "Coverage Ledger"
Cohesion: 0.12
Nodes (12): WorkStatus, SourceEvidence, airport_transfers(), ItinerarySummary, FXSnapshot, LinkScope, ProviderErrorCode, ProviderCapabilities (+4 more)

### Community 2 - "Money and FX"
Cohesion: 0.08
Nodes (19): minor_unit_exponent(), Money, UnknownCurrencyError, ScriptedOutcome, CheckingFake, _query(), test_fake_provider_labels_prices_as_synthetic(), test_fake_provider_respects_idr_zero_minor_units() (+11 more)

### Community 3 - "Provider Failures"
Cohesion: 0.09
Nodes (19): ProviderFailure, aware_iso(), decimal_value(), money(), obj_dict(), stable_id(), exact_http_client(), observe() (+11 more)

### Community 4 - "Measured Production"
Cohesion: 0.14
Nodes (18): MeasuredProduction, ReviewDispatcher, ReviewRepository, TimedFake, drain(), max_overlap(), query(), test_cooldown_occupies_no_execution_slot() (+10 more)

### Community 5 - "Search Service and Demo"
Cohesion: 0.12
Nodes (19): main(), run_demo(), CoverageEntry, unique_covered_combinations(), AirportTransfer, Offer, build_itinerary(), ItineraryGroup (+11 more)

### Community 6 - "Stdlib Imports"
Cohesion: 0.10
Nodes (16): live_guard(), batch(), emit(), main(), provider_run(), migrated(), peak(), percentile() (+8 more)

### Community 7 - "Octotrip Provider"
Cohesion: 0.09
Nodes (16): json_payload(), OctotripProvider, HttpStartGate, test_octotrip_429_stops_unsent_peer_http(), test_octotrip_gate_covers_initialization_across_three_sessions(), respond(), payload(), query() (+8 more)

### Community 8 - "Itinerary UI"
Cohesion: 0.14
Nodes (28): PublicItinerary, PublicOffer, FareRiskNotice(), formatDuration(), ItineraryCard(), BAG_LABEL, COMPARISON_LABEL, describeLink() (+20 more)

### Community 9 - "Settings and Env"
Cohesion: 0.13
Nodes (12): Settings, default_registry(), database(), require_current_schema(), main(), worker_lock(), test_fourth_registration_configuration_and_no_false_capabilities(), test_missing_optional_fli_is_disabled_with_install_reason() (+4 more)

### Community 10 - "Fli Provider"
Cohesion: 0.12
Nodes (19): parse_search_response(), search(), payload(), provider(), query(), test_c3_real_threads_overlap_and_cancel_retains_physical_capacity(), fetch(), test_challenge_redirect_is_not_followed() (+11 more)

### Community 11 - "Runner Dependencies"
Cohesion: 0.15
Nodes (7): live_guard(), main(), run(), main(), main(), main(), main()

### Community 12 - "Web API Client"
Cohesion: 0.12
Nodes (21): dependencies, react@^19.3.1, react-dom@^19.3.1, api, TERMINAL_STATUSES, Created, ExpiredObservation, Results (+13 more)

### Community 13 - "Query and Cache"
Cohesion: 0.12
Nodes (10): lifespan(), cache_key(), OperationAttempt, SearchJob, fixture(), engine(), migrate(), query() (+2 more)

### Community 14 - "API Routes"
Cohesion: 0.10
Nodes (13): create_app(), cancel(), create_search(), get_job(), get_results(), health(), resolve_location(), _exact_reprice_count() (+5 more)

### Community 15 - "Skiplagged and Swoop"
Cohesion: 0.16
Nodes (15): ProviderRepriceResult, SkiplaggedProvider, SwoopProvider, load(), query(), test_missing_zone_retains_unmatched_summary(), test_skiplagged_exact_money_unknown_fields_and_no_fake_segments(), test_skiplagged_request_filters_and_fail_closed() (+7 more)

### Community 16 - "Architecture Docs"
Cohesion: 0.10
Nodes (25): Bounded blocking provider execution, API application domain dependency boundaries, Dependency boundary, 02 — System Architecture and Runtime Boundaries, Durable job and work state, Capability-driven provider abstraction, Provider capability protocols, Fare evidence tiers (+17 more)

### Community 17 - "Location Catalog"
Cohesion: 0.14
Nodes (12): catalog(), fold(), LocationCatalog, MajorResolution, MajorSelection, selection(), test_ambiguous_cities_keep_distinct_ids_and_geography(), test_catalog_rejects_inconsistent_data() (+4 more)

### Community 18 - "API Tests"
Cohesion: 0.18
Nodes (20): client_for(), request_data(), test_api_scheduler_results_contract(), test_auth_and_remote_boundary(), test_baggage_eligibility_and_snapshot_cursor(), test_invalid_input_no_job(), test_openapi_committed_and_response_shapes(), test_quota_and_cancel() (+12 more)

### Community 19 - "Work Log"
Cohesion: 0.10
Nodes (25): Canonical evidence-preserving extensions, Pre-restructure WORK_LOG header (baseline, full tracker, ledger, summary, deviations), 2026-11-09 empty-repo baseline, Historical initial repository and toolchain, FlightFinder renamed CheapWings, P2–P4 implementation log, Historical CGK to CTS cancelled review, P2 recorded acceptance (+17 more)

### Community 20 - "Provider Contracts"
Cohesion: 0.15
Nodes (19): capabilities(), AirportTransfer, Capabilities, Coverage, Created, DTO, ExpiredObservation, Health (+11 more)

### Community 21 - "Throughput Experiment"
Cohesion: 0.12
Nodes (8): Experiment, post(), wrap(), observed(), test_octotrip_three_sessions_share_one_http_gate(), session(), test_response_timing_preserves_stream_bytes(), respond()

### Community 22 - "Alembic Migrations"
Cohesion: 0.14
Nodes (7): upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade()

### Community 23 - "Web Types"
Cohesion: 0.09
Nodes (19): AirportTransfer, ComparisonStatus, Coverage, Currency, IdentityConfidence, Job, JobPhase, JobStatus (+11 more)

### Community 24 - "Search Form"
Cohesion: 0.19
Nodes (16): ProviderCapability, SearchRequest, AirportMultiSelect(), Props, Props, SearchForm(), todayIso(), createLocationService() (+8 more)

### Community 25 - "Itinerary Domain"
Cohesion: 0.15
Nodes (8): compute_fingerprint(), Itinerary, FlightSegment, segments(), test_display_names_do_not_change_itinerary_fingerprint(), test_explicit_airport_change_retains_flight_identity_without_fake_leg(), test_undeclared_or_mismatched_airport_changes_stay_invalid(), test_stops_and_duration()

### Community 26 - "Search Query Model"
Cohesion: 0.15
Nodes (6): QueryValidationError, SearchQuery, plan_scope(), test_boundary_and_overlap_match_expansion(), test_zero_routes_and_date_changes(), admit()

### Community 27 - "Agent Prompt Docs"
Cohesion: 0.10
Nodes (21): Authorized task boundaries, Preserve current baseline, 08 — Starting Prompt for a Local Coding Agent, Implementation invariants, Single reporting location, Dated history is evidence rather than active instructions, Documentation precedence, CheapWings — Worker Implementation Handoff (+13 more)

### Community 28 - "Web Dev Deps"
Cohesion: 0.13
Nodes (19): devDependencies, oxlint@^1.90.0, @types/node@^24.19.2, @types/react@^19.3.0, @types/react-dom@^19.3.0, typescript@~7.0.2, vite@^8.3.6, @vitejs/plugin-react@^6.1.2 (+11 more)

### Community 29 - "tsconfig App"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 30 - "Shortlist Verification"
Cohesion: 0.25
Nodes (12): shortlist(), ComparisonStatus, PriceStatus, ThreeValued, _group(), _offer(), test_hidden_city_excluded_from_default_ranking(), test_lowest_advertised_includes_indicative_but_not_confirmed_hidden_city() (+4 more)

### Community 31 - "Reprice Contracts"
Cohesion: 0.20
Nodes (10): RepriceRequest, SearchProvider, SingleDateRouteQuery, Base, FXRow, ItineraryRow, QuoteRevision, SegmentRow (+2 more)

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
Cohesion: 0.12
Nodes (16): Scheduler design requirements, Authentication and secret boundary, Canonical Money Itinerary Offer Coverage, Coverage and terminal statuses, 04 — Data, Persistence, and REST API Contracts, Normative versioned REST design, Normative versioned REST v1 and canonical DTOs, SQLite persistence schema direction (+8 more)

### Community 36 - "Provider Feasibility Docs"
Cohesion: 0.12
Nodes (17): Exact decimal money and FX provenance, 03 — Provider Feasibility, Multi-Provider Aggregation, and Fare Accuracy, Normalized provider error taxonomy, Itinerary versus seller offer, Conservative itinerary identity and separate fare offers, Comparable exact money, Typed provider failures versus successful empty, P0 provider feasibility gate (+9 more)

### Community 37 - "iOS Client Docs"
Cohesion: 0.12
Nodes (16): Provider feasibility and permission gate, 05 — Web + Native iOS Client Implementation, Polling and recovery design, Web first iOS second, Native SwiftUI implementation plan, Web and SwiftUI share remote search engine, 06 — Worker Implementation Plan, Ordered Checkpoints, and Exit Criteria, Fundamental incompatibility escalation (+8 more)

### Community 38 - "Bounded Calls"
Cohesion: 0.19
Nodes (7): BoundedCall, test_bounded_swoop_executor_c3_has_actual_overlap_and_no_queue(), __init__(), __init__(), __init__(), test_real_thread_slot_retained_on_cancellation(), __init__()

### Community 39 - "Itinerary Tests"
Cohesion: 0.28
Nodes (13): _seg(), test_different_connections_produce_different_fingerprints(), test_identical_segment_sequences_produce_identical_fingerprint(), test_itinerary_requires_connected_segments(), test_segment_requires_tz_aware_datetimes(), _base(), test_include_hidden_city_defaults_false_and_does_not_silently_flip(), test_rejects_excessive_combination_count() (+5 more)

### Community 40 - "P4.11 Fli Log"
Cohesion: 0.16
Nodes (15): Pre-restructure phase summary, Historical usable quote verification, P4.11 — Fli as a fourth provider, Truthful failure and cache semantics, Fourth provider Fli public Google Flights page, P4.11 acceptance evidence, Explicit HTTP2 transport, Indicative Google quotes and generic search links (+7 more)

### Community 41 - "Cache Repository"
Cohesion: 0.23
Nodes (3): CacheRepository, without_handles(), ProviderOperation

### Community 42 - "Observed Provider"
Cohesion: 0.15
Nodes (7): Measurements, ObservedProvider, observers(), make_send(), observed(), post(), utc()

### Community 43 - "Skiplagged Probe"
Cohesion: 0.20
Nodes (6): run(), _utc_now_iso(), main(), run(), _to_jsonable(), _utc_now_iso()

### Community 44 - "Client Errors"
Cohesion: 0.29
Nodes (8): ApiError, BASE_URL, request(), errorMessage(), getOwnerToken(), setOwnerToken(), Capabilities, HTTPValidationError

### Community 45 - "Route Expansion"
Cohesion: 0.35
Nodes (7): expand_routes_and_dates(), RouteDateCombo, _query(), test_1x3x9_expands_to_27_combinations(), test_combos_are_unique_and_deterministic_order(), test_duplicate_input_codes_are_deduplicated_before_expansion(), test_same_origin_destination_pair_is_skipped()

### Community 46 - "Product Requirements"
Cohesion: 0.22
Nodes (10): Accessible responsive UI, 01 — Product Requirements, Rules, and UX Acceptance, One-way adult economy flight finder, Flexible one-way finder scope, Query coverage differs from inventory completeness, Conservative fare ranking, Safe Best checked and Lowest advertised views, Honest results states (+2 more)

### Community 47 - "P46 Browser Tests"
Cohesion: 0.28
Nodes (6): all, dist, job, offer(), richEntries, trip()

### Community 48 - "Dispatch Failures"
Cohesion: 0.22
Nodes (3): DispatchFailure, provider_failure(), test_network_timeout_classification_in_mcp_group()

### Community 49 - "Web Client Docs"
Cohesion: 0.32
Nodes (8): Synthetic browser regressions, CheapWings web, React TypeScript Vite thin client, Runtime private access, Memory-only web owner token, Intercepted Playwright browser regression suite, React Vite thin client, Memory-only web bearer

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

### Community 55 - "Coverage Tests"
Cohesion: 0.60
Nodes (5): _entry(), test_failed_terminal_requires_error_code(), test_failure_is_not_counted_as_covered(), test_succeeded_empty_cannot_carry_error_code(), test_unique_covered_combinations_does_not_double_count_providers()

### Community 57 - "Icon Sprite"
Cohesion: 0.67
Nodes (3): Bluesky, Discord, GitHub and X logos, Reusable SVG icon sprite, Purple documentation and social profile icons

## Knowledge Gaps
- **78 isolated node(s):** `cheapwings`, `Owner access and request admission`, `Snapshot cursor pagination and ranked quote`, `Web document root and TypeScript entry`, `Airportsdata and mwgg Airports MIT attribution` (+73 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 416 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ProviderFailure` connect `Provider Failures` to `Job Runner`, `Coverage Ledger`, `Bounded Calls`, `Octotrip Provider`, `Stdlib Imports`, `Fli Provider`, `Runner Dependencies`, `Observed Provider`, `Skiplagged and Swoop`, `Dispatch Failures`, `Throughput Experiment`, `Reprice Contracts`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Are the 78 inferred relationships involving `Repository` (e.g. with `AirportTransfer` and `IdentityConfidence`) actually correct?**
  _`Repository` has 78 INFERRED edges - model-reasoned connections that need verification._
- **What connects `cheapwings`, `Owner access and request admission`, `Snapshot cursor pagination and ranked quote` to the rest of the system?**
  _78 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Job Runner` be split into smaller, more focused modules?**
  _Cohesion score 0.055262968039823966 - nodes in this community are weakly interconnected._
- **Why does `FakeProvider` connect `Job Runner` to `Coverage Ledger`, `Money and FX`, `Measured Production`, `Search Service and Demo`, `Settings and Env`, `API Tests`, `Itinerary Domain`, `Shortlist Verification`, `Reprice Contracts`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Are the 39 inferred relationships involving `ProviderFailure` (e.g. with `JobRunner` and `ExactCapture`) actually correct?**
  _`ProviderFailure` has 39 INFERRED edges - model-reasoned connections that need verification._
- **Should `Coverage Ledger` be split into smaller, more focused modules?**
  _Cohesion score 0.11740041928721175 - nodes in this community are weakly interconnected._