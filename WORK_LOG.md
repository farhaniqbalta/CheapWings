# WORK_LOG.md — Worker Progress Tracker

This file is the source of truth for current phase status, implementation decisions, provider approvals, validation evidence, blockers, and the exact next task. **All provider reports, live-result assessments, UI/UX handoff reports, test summaries, and release reports belong in this file. Do not create separate report files.** Static specifications/prompts, code, contracts, fixtures, and screenshots can remain separate artifacts linked from here. Checkpoint entries below are historical; use the phase tracker and latest checkpoint summary for current status.

## Project baseline
- Date: 2026-11-09
- Repository/branch: initialized fresh (`git init`), branch `main`, root commit `88a4f83` (handoff docs only)
- Existing code found: none. Workspace contained only `docs/` (the worker handoff spec: `README.md`, `01`–`08`, `WORK_LOG_TEMPLATE.md`, `reference/V4_FULL_DESIGN_REFERENCE.md`). No backend/frontend/iOS code, no root `README.md`, no `.env.example`.
- Note: `08_AGENT_START_PROMPT.md` refers to a `CheapWings_Worker_Handoff/` directory; the actual docs live directly under `docs/`. Treating `docs/` as that directory — no content discrepancy, just a path naming difference in the prompt text.
- Commands attempted (environment probe, 2026-11-09):
  - `python3 --version` → 3.9.6 (system). Need 3.12+ per non-negotiable #1 — not yet installed.
  - `node --version` / `npm --version` → not found. Need for React/Vite — not yet installed.
  - `git --version` → 2.50.1 (Apple Git-155), available.
  - `brew --version` → Homebrew 7.0.12, available for later toolchain install (Python 3.12, Node) — owner asked to hold off for now.
  - `xcode-select -p` → `/Library/Developer/CommandLineTools` only; full Xcode not installed. Blocks real SwiftUI project builds at P5; not a P0–P4 blocker.
  - `curl` reachability: `skiplagged.github.io` → 200, `github.com` → 200, `pypi.org` → 200. Network egress confirmed available for P0 research/probing.
- Decisions/ADRs:
  - 2026-11-09: Project renamed from "FlightFinder" to **CheapWings** per owner instruction (matches the working directory name). All active docs (`docs/01`–`08`, `docs/README.md`, this file) updated accordingly. `docs/reference/V4_FULL_DESIGN_REFERENCE.md` intentionally left verbatim/unrenamed — it is explicitly retained as historical record, not an active instruction source. Future package/module names (`cheapwings` instead of `flightfinder`) should follow this rename once code exists.
  - 2026-11-09: Owner asked to pause before installing the Python 3.12/Node toolchain or running live P0 provider probes in the prior checkpoint; owner then said "continue" and toolchain install + live P0 probing were executed in this checkpoint (see below).
  - 2026-11-09: Installed Python 3.12.16 and Node v26.13.0 via Homebrew (`brew install python@3.12 node`). Created throwaway `.venv_probe/` (gitignored) with `mcp` 2.3.0 and `swoop-flights` 0.7.0 for P0 probing only — not the final backend venv.

## Phase tracker
| Phase | Status | Evidence | Blocking issue | Next action |
|---|---|---|---|---|
| P0 Provider feasibility | Done (owner-accepted personal-use GO both providers) | [provider feasibility evidence](#provider-feasibility-evidence); redacted fixtures in `contracts/fixtures/provider/`; `scripts/provider_probe_skiplagged.py`, `scripts/provider_probe_swoop.py` | None for accepted personal scope; revisit before public/commercial use | P3 adapter integration |
| P1 Domain + fake provider | Done | `backend/src/cheapwings/{domain,engine,providers}`, 42 passing tests, `python -m cheapwings.cli_demo` offline demo | None | Start P2 — SQLite persistence, durable scheduler, REST API |
| P2 Durable jobs + API | Done | 72 passing tests at P2, migrations/no schema drift, OpenAPI, runbook. `python scripts/p2_smoke.py` now actually run (see below) — real process launch, worker kill/restart mid-job, 3/3 covered, 6 distinct offers, no duplicate attempts | None | — |
| P3 Real providers + repricing | Done (offline + live canary); real-world usage still opt-in | 85 passing tests incl. an integration test that replays real redacted P0 fixtures through the production adapters end-to-end; live canary run through the actual adapter classes (not raw SDK) in this session | None blocking; `ENABLED_PROVIDERS` still defaults to `fake` | Owner can flip `ENABLED_PROVIDERS=skiplagged,swoop` for real personal use whenever ready; otherwise start P4 |
| P4 React web | Done; owner live web test running | Base d0ff8b3 + pushed follow-up 339307d; 85 backend, 3 frontend tests, build, 4 browser scenarios passed | None blocking local web test | Owner test feedback; P4.5 UI/UX handoff |
| P4.5 UI/UX refinement | Brief and integration contract prepared; design implementation pending | docs/P4_5_UI_UX_AGENT_PROMPT.md; docs/P4_5_UI_UX_INTEGRATION.md | Await UI/UX agent output | Integrate focused React/CSS patch with preserved API/hook behavior and validation |
| P5 SwiftUI native iOS | Not started | | | Full Xcode required, only CLT present |
| P6 Release acceptance | Not started | | | |

## Provider decision ledger
| Provider | GO/CONDITIONAL GO/NO-GO | Permission/terms | Tested version + date | Missing fields/risks |
|---|---|---|---|---|
| Skiplagged MCP | **GO (personal/single-owner use)** — owner accepted 2026-11-09 | Site terms (`skiplagged.com/terms`) ban commercial use/redistribution/scraping; `sk_faq_search` found no MCP-specific permission. Owner explicitly confirmed: acceptable as long as the project stays personal/non-redistributed; revisit (seek written permission) before any public/multi-user launch. | `mcp` SDK 2.3.0, probed 2026-11-09 | No exact-reprice tool exists at all (10 tools listed, none is repricing). No per-segment flight-number data for connecting itineraries (`layovers≥1` → `insufficient_identity`). No fare brand/seller/baggage fields. Hidden-city `attributes` tag string still unconfirmed (no hidden-city fare surfaced in the probed route/date even with `includeHiddenCity=true`). |
| swoop | **GO (personal/low-volume use)** — owner accepted 2026-11-09 | MIT-licensed library, but calls Google's undocumented internal RPC with browser TLS impersonation — standard Google ToS risk for unauthorized automated access (contract-violation risk, not verified-quote; realistic consequence is blocking/breakage, not legal action, at hobby volume). Owner explicitly accepted this risk for a personal project. Revisit if this ever scales/commercializes. | `swoop-flights` 0.7.0, probed 2026-11-09 | No hidden-city signal at all (`hidden_city` must always be `unknown` for swoop offers). `price_selector()` returned `is_estimate=True` on the one live call — can't assume `repriced_exact` without further testing on more itineraries. Top-level `is_basic_economy` can disagree with individual `booking_options[].is_basic` — must key offers off `booking_options`, not the top-level flag. |

## Latest checkpoint summary
- **P4.5 handover branch:** `p4.5-ui-ux-handoff`, created from main at `532f080` on owner instruction. This branch contains consolidated reporting and the UI/UX handoff; no P4.5 redesign code has been implemented. Read the P4.5 handover task section below before editing.
- Reporting rule updated by owner: all provider evidence, test/release reports and UI/UX handoff findings live here. Complete P0/P3 provider evidence has been merged under Provider feasibility evidence; standalone report removed. Active specs/prompts no longer instruct agents to create report files.
- Latest owner review: inspected the saved CGK → CTS real search in Chromium and read-only storage. It was cancelled at 36/78 covered dates with 954 advertised offers, 14 swoop schema failures and zero reprice work. Safe ranking is correctly empty; review priorities and returned-price examples are recorded in the owner live-results review section. No new upstream calls or application changes were made.
- Phase: P4 implemented and follow-up browser acceptance passed; P4.5 UI/UX handoff requested by owner and prepared. Web follow-up pushed to `origin/main` as `339307d` (git push succeeded). Earlier sandbox-blocker entries below are historical; escalated operations now allow Git/browser/server execution in this session.
- Validation: 85 backend tests, 3 frontend tests and TypeScript/production build passed in the follow-up. `npm run test:browser` now actually passed **all four scenarios**: empty-safe → advertised + pagination/reload, runtime auth, expiry, and cancellation with retained fares. Current browser suite viewport is 375px; earlier base-P4 visual checks at 375/768/1440 remain recorded. No new wider-viewport screenshot claim.
- Launched fake API+worker+web first as requested; actual HTTP/CORS + 2-combination synthetic worker search passed. Then owner explicitly requested real data: stopped fake API/worker, migrated isolated `data/webtest-live.db`, updated ignored local `.env` to `ENABLED_PROVIDERS=skiplagged,swoop`, `CHEAPWINGS_USE_SCOPE=personal`, and restarted both services. Existing secrets preserved; `.env` is mode 0600 and must never be committed. Tracked env examples still default to fake.
- Live wiring verified over HTTP: web 200; capabilities `synthetic_mode=false`; both Skiplagged and swoop enabled with pinned dependencies present. No additional live provider probe submitted by this agent during the switch; actual live fare outcomes depend on the owner's searches. Use Lowest advertised for indicative/risk-unknown fares; never relax safe ranking to populate a screen.
- Running services: web `http://localhost:5173/` (session 70252, PID 81275); live API `http://127.0.0.1:8000` (session 35644, PID 81757); live worker session 6239. Leave these running for the owner's test. Old fake sessions 69133/80467 were stopped. Original fake DB `data/webtest.db` preserved separately. Browser opened on fresh root search page, not a fake job URL.
- P4.5 artifacts: `docs/P4_5_UI_UX_AGENT_PROMPT.md` is the copy-ready designer prompt; `docs/P4_5_UI_UX_INTEGRATION.md` defines file/behavior boundaries, acceptance cases and designer-return template. WORK_LOG.md remains the sole progress/decision source. Webview work refines React; native SwiftUI P5 remains required.
- Next smallest task: UI/UX agent uses `p4.5-ui-ux-handoff` and the P4.5 prompt/integration guide, implements the presentation task checklist below in an isolated checkout, and appends its return evidence here. Implementation agent reviews/integrates and validates before P4.5 acceptance. Keep the owner's running live test unchanged; use fake/intercepted data for design QA. Full Xcode remains required for P5 build/simulator acceptance.

## Explicit deviation log
| Date | Approved design changed | Reason/evidence | Owner decision needed? |
|---|---|---|---|
| 2026-11-09 | Extend canonical itinerary with an explicit incomplete summary; add nullable offer metadata and source/FX evidence | P0 Skiplagged connecting flights lack segments; swoop local segment times need validated timezone reference. Existing P1 nonempty complete-segment-only representation cannot preserve these candidates honestly. Keep complete-segment behavior unchanged; never fabricate legs, timezones or fare fields. | No — within approved canonical unknown/insufficient-identity requirements |
| 2026-11-09 | Add P4.5 web UI/UX refinement between P4 and P5 | Owner explicitly requested a UI/UX-agent brief for the webview and later integration. Presentation scope only; retain React/API and genuine native iOS P5. | Already authorized by owner |

## P2 implementation decisions

P1 domain, matching, ranking and fake provider code are unchanged. These decisions
refine the illustrative contract before clients ship; none changes product scope.

- Public request uses the documented nested `passengers` and nullable integer
  `max_stops`; an application DTO converts these to existing P1 fields. Clients
  cannot supply `max_combinations`. Query snapshots use canonical P1 JSON.
- Public response DTOs live in `application/contracts.py` so the API depends on
  application projections and application never imports FastAPI or the API layer.
- Canonical segments and offers use versioned JSON alongside relational identity,
  FK and uniqueness keys. Original/comparable monetary fields also have explicit
  decimal-text columns. FX/revision tables exist; live conversion/repricing is P3.
- Quote IDs exposed to clients are database quote IDs; upstream IDs are separately
  scoped by job/provider. Offers remain separate even if provider IDs collide.
- Atomic BEGIN IMMEDIATE claims plus a single POSIX queue-owner lock; global
  provider concurrency and persisted next-request/cooldown timestamps. Calls happen
  outside transactions. Worker-local active task counts also retain slots for
  cancelled but unfinished calls. Database errors stop the worker visibly.
- Cancellation is immediately terminal in P2. Pending/running leases are invalidated;
  completed quotes persist, late responses are discarded. Only expired running
  leases can be reclaimed after a crash, and every attempt has a durable record.
- Default global job budget is 1800 wall-clock seconds from creation. Retry maximum
  is three attempts; exponential delays are 1/2/... seconds capped at 60, with
  Retry-After a lower bound. Provider-wide cooldown persists across worker restarts.
- Single-owner auth with a shared bearer token protects all search operations for
  remote/private deployment. Unauthenticated mode checks client loopback address
  and Host. Creation limits are global to that owner and atomically enforced.
- Cursor pagination fixes a maximum immutable quote-row ID and ordering snapshot;
  later results require a fresh first-page request. `ranked_quote_id` explains group
  ordering while every seller retains its own classification. Currency-mismatched,
  explicitly ineligible and changed/unavailable quotes never determine ordering.
- New API boundary handles expired dates and supported currencies without modifying
  P1. Airport existence and precise origin-local expiry require airport reference
  data (not fabricated in P2); current expiry uses server date, a known limitation.
- No live provider data is stored in P2; default fixtures clearly say synthetic.
  Terms-dependent live cache/selector/evidence retention remains a P3 gate.

Process smoke is available as `scripts/p2_smoke.py`. It launches Uvicorn and a
separate worker, kills/restarts the worker after the first successful combination,
and checks all three combinations/six distinct offers without rerunning success.
This managed session cannot bind sockets; that process-level gate remains unverified
here. Equivalent durable recovery/fencing/commit invariants run in pytest.

## P2 kickoff record (2026-11-09; historical)
- Owner authorized all of P2, including incremental commits. Read active docs in order and P0 report; baseline suite: 42 passed. Working tree initially clean; no AGENTS.md found.
- Implementation underway, no P1 domain changes authorized/needed. Three checkpoints: (1) SQLite models/migrations + atomic job storage; (2) separate durable worker with lease fencing, shared provider pacing/retries/cancel; (3) REST v1, typed OpenAPI, auth/quotas, integration tests/runbook.
- First acceptance: migration up/down on temporary DB, WAL/FK/uniqueness, immutable query snapshot and complete unique matrix created atomically.
- Runtime choice: separate single-owner worker process, never request BackgroundTasks. Default registry is synthetic fake only. Real adapters remain P3. Public API will require a configured owner bearer token; loopback-only development can omit it.
- Next action: implement persistence and migration tests, run full suite, update checkpoint summary and commit. No live probes or permission decisions to repeat.

### P2 checkpoint 1 — persistence (complete)
- Files: storage models/db/repository; initial versioned Alembic migration and config; adapter registry; integration storage test; runtime DB ignore rules.
- Evidence: `.venv/bin/python -m pytest backend/tests -q` → 43 passed. Migration upgrade/downgrade/upgrade, WAL/FK/busy timeout, work uniqueness and orphan rejection, immutable query snapshot, full 54-item matrix with 27 explicit disabled entries tested.
- Decisions: money stored as decimal text, canonical segment/offer fields additionally stored as JSON; server timestamps use integer UTC epoch milliseconds. Query snapshot stored separately from mutable domain input. SQLite BEGIN IMMEDIATE serializes short writes and quota checks. P1 unchanged.
- Next smallest task: implement fenced lease claims, attempt ledger, result commit transaction and worker recovery/cancellation tests.

### P2 checkpoint 2 — durable worker (complete)
- Files: repository claim/sweep/finish/result transaction; attempt ledger; persisted provider cooldown migration; job_runner; settings; separate worker command with exclusive POSIX file lock.
- Tests: `.venv/bin/python -m pytest backend/tests -q` → 52 passed. Evidence covers 54 work items/two providers with partial failure and empty success, atomic competing claims, restart after completed pairs, stale lease fencing, result commit rollback, bounded attempts, 120-second Retry-After, timeout classification, job deadline exhaustion, idempotent cancellation preserving completed quotes.
- Decisions: claim uses BEGIN IMMEDIATE; persisted provider running count enforces global concurrency across jobs, persisted next_request_at enforces pacing/cooldowns. Lease exceeds call timeout. Stale leases are recovered on every tick, never before expiration. Quotes and terminal success commit together; duplicate provider quote IDs scoped to job/provider. Exact selector remains server-only.
- P1 domain unchanged. Application maps required baggage/stop/basic constraints to comparison eligibility when persisting results. Fake fares remain visibly synthetic. Repricing remains P3.
- Commit blocker: `git add` and `git commit` both failed with `Unable to create .git/index.lock: Operation not permitted`. Managed filesystem exposes `.git` read-only; no commits created in this session. Continue authorized work; leave descriptive proposed commit messages for owner/next writable session.
- Next smallest task: REST v1 with typed canonical responses, owner auth and creation quotas, stable snapshot pagination/OpenAPI generation and end-to-end acceptance. Also verify worker executable and document migration/startup.


### P2 checkpoint 3 — REST/OpenAPI and final handoff
- Implemented: health/capabilities, durable POST searches (202 + Location), GET status with complete coverage ledger, grouped paginated results, idempotent cancel, OpenAPI at `/api/v1/openapi.json`. Public requests follow docs/04; application DTO maps nested passengers/nullable stops to existing P1. Owner token required for remote requests; direct loopback development permitted; restricted CORS and atomic active/hourly creation quotas.
- Runbook: root README documents two-process startup, migration requirement, env sourcing, auth, snapshot pagination, budgets, restart/cancel semantics, blocking-thread constraints, evidence retention and known limits. `.env.example` defaults to fake only. OpenAPI exporter commits JSON syntax valid as YAML 1.2.
- Additional findings fixed: cancelled in-flight provider calls must keep worker-local concurrency slots; larger configured combination caps must survive immutable query snapshots; unsafe/malformed external links become unavailable; missing/outdated DB schema rejected by API and worker.
- Decisions/refinements documented in [P2 implementation decisions](#p2-implementation-decisions) in this work log. Segment/offer canonical JSON supplements relational keys/constraints and explicit decimal-text monetary columns. Persistent DB claim counts + local task slots serve as global provider concurrency guard rather than an additional redundant semaphore. Separate worker has exclusive POSIX flock ownership.
- Known limits: airport existence/reference and exact origin-local expiration are not invented; P2 validates code shape and uses server date for expiry. Real cache/evidence/selector TTL and repricing belong to P3 before live persistence. Synthetic data currently persists until owner removes the stopped local DB. No provider raw payloads/PII stored.
- Final verification: 72 pytest tests pass; Ruff passes on all new P2 Python; migration upgrade/downgrade/upgrade covered in temporary DBs; `alembic check` reports no new operations; original CLI works. Existing P1 lint nits retained. Upstream TestClient deprecation is a warning, not a failure.
- Process acceptance: script provided but socket bind denied by sandbox before API launch. Pytest exercises restart/recovery and single-worker ownership; **real process launch/kill/restart remains unverified in this session**.
- Commit delivery blocked by read-only `.git`. Suggested reviewable commits for a writable session:
  1. `P2: add SQLite schema, Alembic migrations and atomic job storage`
  2. `P2: implement leased worker, persistent provider budgets and restart recovery`
  3. `P2: expose authenticated REST v1 and OpenAPI with offline acceptance tests`
  Include relevant WORK_LOG checkpoint evidence in each, or use one final P2 implementation commit if historical splitting is impractical. No destructive git workaround attempted.
- Exact resume command: `.venv/bin/python scripts/p2_smoke.py` from repository root. It uses a temporary migrated DB, fake fares, real Uvicorn and a separate worker; kills/restarts after first success; expects 3 covered combinations, 6 distinct offers, no duplicate attempts on completed work. No upstream network calls.

### Owner requested push (2026-11-09)
- Requested push of P2 to `origin/main`; verified branch `main`, remote `https://github.com/farhaniqbalta/CheapWings.git`, local HEAD `a3809e5`.
- Retried staging the exact P2 files: denied creating `.git/index.lock` (Operation not permitted). Cannot create the local commit in this sandbox.
- Checked connected GitHub fallback: repository lookup returned 404/NOT_FOUND for this private repository, so the connector cannot publish it either.
- No commit or push performed. P2 files remain intact in the working tree. Next action remains unrestricted local commit/push and process smoke.

### Documentation consolidation (2026-11-09)
- Owner requested WORK_LOG.md as the single source of truth. Merged all P2 implementation notes into the P2 implementation decisions section above and removed the separate notes file. Updated references and labeled the kickoff record historical to prevent stale next-action instructions overriding the latest checkpoint summary.
- Documentation-only change; P2 implementation, pending process smoke, and commit/push blockers are unchanged.
- Validation after consolidation: all original P2 notes preserved; no remaining references to the removed file; `git diff --check` passed; backend suite **72 passed** with the existing upstream TestClient deprecation warning.

### Push retry after documentation consolidation (2026-11-09)
- Owner requested push and next-task report. Retried staging the consolidated P2 implementation and WORK_LOG.md; `.git/index.lock` creation is still denied (Operation not permitted), so no local commit or push was possible. Local HEAD remains `a3809e5`; all changes remain intact.
- Next task remains P2 process acceptance: `.venv/bin/python scripts/p2_smoke.py` in an unrestricted terminal, then commit/push and mark P2 Done on success. Next implementation phase is P3: fixture-backed Skiplagged/swoop adapters, conservative normalization, live-data retention policy, and exact-offer repricing where supported. P0 personal-use approvals are already resolved.

## P3 kickoff (2026-11-09)
- Read WORK_LOG and P3 checkpoints; inspected P0 fixture schemas, SDK 0.7.0 source in throwaway venv, existing queue/storage/API. Checked current official provider documentation as supporting reference; versioned P0 schemas remain integration baseline.
- Implementation worker must keep this file updated with actual file/test evidence and exact resume action. No separate implementation-notes document.

### P3 checkpoint 1 — adapter normalization and canonical evidence
- Added canonical `ItinerarySummary`, `SourceEvidence`, normalized provider errors, optional basic-economy metadata, and reprice request/result types. P1 complete-segment behavior unchanged; extension justified in deviation log.
- Added Skiplagged adapter normalization of original USD + per-quote Decimal FX, upstream hidden-city/virtual-interlining exclusion, unknown seller/fees/basic economy, unmatched summaries. Even nonstop cards remain conservatively unmatched because operating-carrier identity is not provided.
- Added swoop adapter with bounded one-thread execution retaining its actual slot after await cancellation, per-request TransportConfig (20s HTTP timeout, SDK retries=0), unknown hidden-city classification, seller-option-level basic fare handling, estimate-aware pricing, and explicit airport-reference/DST ambiguity handling.
- P0 fixture discovery: swoop's 11 returned candidates include **one with no price/currency**. Count unpriced candidates explicitly; never invent a price or silently treat the response as no flights.
- Added exact MCP JSON/SSE capture before SDK Any fields become binary floats; ephemeral bounded capture only, no payload persistence/logging. Added optional pinned live dependencies: mcp==2.3.0, swoop-flights==0.7.0, airportsdata==20261103 (reference package release verified on PyPI).
- Added migration `1cf9a06e0e54` for summaries/evidence/provenance, verification state, retention deadline and unpriced counters. Uses nullable inline SQLite REFERENCES and defaults to preserve populated P2 databases.
- Tests at this checkpoint: `.venv/bin/python -m pytest backend/tests -q` → **80 passed**, existing upstream warning. Eight adapter tests use P0 recorded evidence/injected transports; no external provider calls.
- Network: `curl https://pypi.org/pypi/airportsdata/json` failed DNS resolution in sandbox. Live dependency installation and live adapter canary not validated. Official docs browsed via web tool for SDK/reference context only, not a successful provider call.
- Next smallest task: wire summary/evidence projections, policy-gated registry, durable reprice shortlist/revision snapshots and live-data expiration; add integration tests before enabling live configuration.

### P4 checkpoint 1 — React web client (2026-11-09)

**Status: implementation complete and visually verified; session paused here for token budget before README update and final commit/push.**

- Scaffolded `apps/web` with `npm create vite@latest -- --template react-ts` (React 19, Vite 8, TS ~7.0.2). `openapi-typescript` could not be installed (its peer range wants TS `^5.x`, this scaffold has `~7.0.2`) — hand-wrote `src/api/types.ts` directly from `contracts/openapi.yaml`'s actual schemas (not the illustrative docs/04 examples), including `SearchRequest`'s nested `passengers`/nullable `max_stops`, `PublicOffer`'s optional evidence fields (`fee_completeness`, `fx_rate`, `fx_as_of`, `attribution`), and `ThreeValued`/`PriceStatus`/`ComparisonStatus`/`LinkScope` enums verbatim.
- `src/api/client.ts`: single typed fetch module (`api.health/capabilities/createSearch/getJob/getResults/cancelSearch`), optional `VITE_OWNER_TOKEN` bearer header for non-loopback deployments, `ApiError` surfaces `HTTPValidationError.detail` messages.
- Hooks (plain `useState`/`useEffect`, no TanStack Query/Redux — not justified at this size per docs/05): `useJobPolling` (job-status timer 2s→10s backoff, stops at terminal status or unmount; a **separate** effect refetches results keyed on `job.updated_at`/sort so toggling sort never restarts the job-status timer — this was a deliberate fix after a first draft coupled them and would've reset visible job state on every sort click), `useCreateSearch`, `useCancelSearch`.
- Components: `AirportMultiSelect` (chip entry, client-side IATA shape check only, no fabricated airport-name lookup), `SearchForm` (combination-count preview, hidden-city opt-in with explicit risk copy, client validation mirrors server rules but server is source of truth), `SearchProgress` (status pill, phase, coverage, per-provider succeeded/failed/cancelled/skipped, cancel button, reprice counts, warnings), `ResultSortBar`, `ItineraryCard` (expandable segments, `insufficient_identity` warning banner), `OfferList`, `PriceStatusBadge` (text label always accompanies color), `FareRiskNotice` (hidden-city/self-transfer/baggage-unknown/missing-required-baggage/currency-unresolved, all three-valued states handled explicitly, `unknown` never silently treated as safe), `JobErrorPanel` (distinguishes transport error vs `failed` vs `partial` vs `cancelled`). Money displayed via `lib/money.ts` which formats the decimal **string** with regex thousands-grouping — never parsed through `Number`, so display can't introduce float error even though it's not a calculation path.
- `App.tsx`: job id kept in the URL query string (`?job=...`, not localStorage) for refresh/recovery without re-creating a search; empty-state copy distinguishes "no matching fares in searched sources" from a hard `failed` job.
- **Build verification:** `npx tsc -b` clean (fixed one unused-import error). `npm run build` clean (`tsc -b && vite build`, 237KB JS / 6.4KB CSS gzipped).
- **Contract verification against the real backend** (not mocked): started the actual `uvicorn cheapwings.main:app` + `python -m cheapwings.worker` with the fake provider, `curl`'d `POST /searches` → `GET /searches/{id}` → `GET /searches/{id}/results?sort=best_checked` and diffed the JSON shape against `src/api/types.ts` by hand — exact match, including `passengers.adults`, decimal-string prices, and all evidence fields. Confirmed CORS (`Access-Control-Allow-Origin: http://localhost:5173`) works against the real server with the default `.env.example` origin.
- **Visual/E2E verification:** `chromium-cli` (the skill's preferred driver) is not installed in this environment; fell back to `npx playwright install chromium` + a throwaway Playwright script (not committed) driving the real Vite dev server against the real backend. Filled the form (MEL→CGK, Dec 12–14 2026), submitted, waited for completion, screenshotted at 375/768/1440px. **Found and fixed a real desktop-only bug this way:** the itinerary card used a 2-column CSS grid but only the header/segments were assigned `grid-column: 1/-1`; `OfferList` fell into the implicit first column at 1440px, leaving the entire right half of every card blank. Replaced the per-card 2-column grid with an internal `auto-fit` grid on `.offer-list` itself (offers wrap into columns inside one full-width card) — re-verified screenshot shows offers laid out correctly in two columns with no dead space. Zero console/page errors at any width after the fix.
- **Not yet done:** root `README.md` doesn't yet document `cd apps/web && npm install && npm run dev` / `.env.example` copy step. `apps/web` is implemented but **not committed or pushed** — this checkpoint was written and committed first, per owner request, to protect the work before continuing was token-constrained.
- Exact resume: `cd apps/web && npm install && cp .env.example .env && npm run dev` (needs the backend API+worker running per root README). Then: update root README with web instructions, `git add apps/web .gitignore WORK_LOG.md`, commit, push.

### P3 completion record (historical)
- Phase: P3 complete (offline implementation + live canary). This session resumed in a *writable* sandbox (unlike the prior agent's read-only `.git`): committed the P3 checkpoint-1 work that was sitting uncommitted (adapters, evidence, reprice, registry, migration — commit `9c05a20`), then closed the two gaps the WORK_LOG flagged as unverified.
- **P2 process smoke, finally run:** `python scripts/p2_smoke.py` → `{"status": "completed", "worker_restarted": true, "completed_before_restart": 1, "covered_after_restart": 3, "distinct_offers": 6, "all_prices": "SYNTHETIC-FIXTURE-NOT-A-REAL-FARE"}`. Real Uvicorn + separate worker process, killed and restarted mid-job, no duplicate attempts on already-completed work. P2's previously-unverified process-level gate is now closed.
- **P3 live canary, through the real adapter classes:** installed pinned `backend[live]` deps (`mcp`==2.3.0, `swoop-flights`==0.7.0, `airportsdata`==20261103) and ran `scripts/p3_live_canary.py` (new, not a raw-SDK probe like the P0 scripts — calls `SkiplaggedProvider.search()` / `SwoopProvider.search()` / `SwoopProvider.reprice()` directly). Both adapters parsed live responses cleanly with no exceptions; swoop's live call reproduced the exact "1 unpriced candidate" quirk found in the P0 fixture, confirming the adapter's `unpriced_candidate_count` handling is correct on fresh data, not just the frozen fixture. Full detail and redacted evidence in [provider feasibility evidence](#provider-feasibility-evidence)'s new "P3 live canary" section. Raw script output (contains swoop's opaque selector) was not committed, per evidence-retention rules.
- On inspection, the code already uncommitted from the other agent's session covered **far more of P3 than its own "next smallest task" note suggested**: durable reprice shortlist (`storage/verification.py::schedule_verification`), append-only quote revisions, live-data retention/expiry+purge, policy-gated registry (`permitted_to_aggregate` tied to `CHEAPWINGS_USE_SCOPE`), and full API/evidence projection wiring were all already implemented and wired into `JobRunner.tick()`. The "next smallest task" text in the prior checkpoint was stale relative to the actual diff; don't trust a "next task" line over reading the code when picking up another agent's unfinished session.
- Baseline/final: `.venv/bin/python -m pytest backend/tests -q` → **85 passed** (same as inherited, confirmed stable through this session's changes). `ruff check` → 8 pre-existing cosmetic nits (unsafe-fix-only), no correctness issues.
- `ENABLED_PROVIDERS` still defaults to `fake` in `.env.example` — real personal use requires the owner to explicitly set `ENABLED_PROVIDERS=skiplagged,swoop` (and `CHEAPWINGS_USE_SCOPE=personal`, already the default) when ready; nothing in this session changed that default.
- Provider permissions remain owner-accepted for personal/non-redistributed use; this session's live canary doesn't change that scope, it just confirms the production code path works, not just the SDK.
- Next smallest task: owner decides whether to start using live providers now (flip `ENABLED_PROVIDERS`) or move on to P4 (React web client) with `fake` still default; either is unblocked.


### P4 checkpoint 2 — runbook and reliability/security follow-up (2026-11-09)
- Resume inspection found base P4 already committed in `d0ff8b3`, despite the old checkpoint saying uncommitted. Preserved prior P3 completion evidence as historical record and refreshed latest summary/phase tracker.
- `src/api/errors.ts` handles FastAPI string detail (401/404/410/429) as well as arrays without `.map` exceptions. Request paths encode job IDs. Runtime `src/api/session.ts` stores owner bearer token only in memory; App offers password input and reconnect, with no VITE token/env/browser storage/URL persistence. Refresh retains job URL but needs token re-entry for authenticated servers.
- `useJobPolling` separates status, result and pagination errors; fences stale pages across job/sort/access changes; clears previous result scope; provides load-more and explicit retry. App exposes sort even when best-checked is empty, so risk-unknown P3 offers remain inspectable via advertised view. Cancel errors are surfaced, and a cancel response triggers status refresh. Existing partial results remain displayable.
- `OfferList` shows provider attribution, nullable fare metadata and original amount/FX evidence. `lib/time.ts` formats source-local date/time and explicit UTC offset, or labels unresolved timezone; flight dates no longer shift to the viewer's timezone.
- Root README now documents all three processes, pinned optional live providers, real retention behavior and memory-only web credentials. Replaced scaffold web README, corrected env templates, added `npm test` and `npm run test:browser` scripts. Default source remains fake.
- Tests: 85 backend + 3 frontend pass; production TS/Vite build passes. New browser suite uses Playwright to serve built assets and synthetic APIs via interception (no server/provider network needed), but process startup is denied by this managed sandbox. Tests cover both string error cases and original-local time rendering at unit level; browser state/interaction scenarios remain pending actual run.
- Scope: local-only Sites skill workflow, no hosting registration/deployment, no provider-policy change, no P1/P3 backend changes. P5 remains separate and requires full Xcode for real build acceptance.
- Commit attempt in this follow-up: `git add README.md .env.example WORK_LOG.md apps/web` failed creating `.git/index.lock` (Operation not permitted). No follow-up commit/push created. Base HEAD remains `d0ff8b3`; all follow-up changes remain in working tree. Suggested commit after browser checks: `P4: harden web auth, result recovery and pagination; complete runbook`.

### P4 launch, live-data switch and P4.5 handoff (2026-11-09)
- Git restrictions resolved through approved escalated tool execution: staged, committed P4 follow-up as `339307d`, pushed `origin/main` successfully. No force push or history rewrite.
- Fake launch acceptance: API, worker and Vite started; CORS accepted localhost:5173; a two-combination job completed with 2 result groups. The four new production-bundle Playwright regression scenarios all passed. These checks made no upstream provider calls.
- Owner then requested real data. Verified `mcp==2.3.0`, `swoop-flights==0.7.0`, `airportsdata==20261103`; both registry sources enabled. Local `.env` now selects personal live sources and `sqlite:///./data/webtest-live.db`, with 20 reprice budget and 3600s live retention; never expose or commit this file. Started real worker/API and verified non-synthetic capabilities; reopened browser at root search page. Fake data remains isolated in its old database.
- Added two P4.5 handoff documents: copy-ready UI/UX prompt, integration boundaries/checklist and return template. The designer must deliver edits to existing React components/CSS, preserve backend ranking/money/unknown semantics and tested auth/recovery/pagination, use synthetic design evidence, and leave backend/contracts/provider configuration intact. No redesign implementation or P4.5 acceptance is claimed yet.
- Updated documentation references and current phase tracker. Next: owner live test and designer output, then implementation-agent integration/validation. Keep the running local services available; do not restart them in fake mode while the owner is testing live.

### Owner live-results review — CGK → CTS (2026-11-09)
- Owner requested assessment only; inspected saved live job `7bdc5913-67a1-43df-9aee-f77037cd1f06` in read-only SQLite and rendered that same job in an isolated Chromium page at 1440px and 375px. Did not change owner's tab, submit searches, call upstream sources, alter ranking, or expose private handles. Review screenshots/text are ephemeral `/tmp/cheapwings-review-*`; do not commit live fare payloads/screenshots as design fixtures.
- Request: CGK → CTS, 2026-12-13 through 2027-02-28 inclusive (78 dates), one adult/economy/IDR, include-basic-economy=true, checked bag not required, include-hidden-city=true. Job cancelled after 541s; 36/78 unique dates covered, spanning Dec 13–Jan 17. Remaining dates are unsearched, not proven expensive/unavailable.
- Detailed work: Skiplagged 35 results + 1 successful empty + 42 cancelled; swoop 21 results + 14 schema_changed failures + 43 cancelled. Swoop recorded 18 unpriced candidates. Full provider inventory remains unknown; all 35 Skiplagged result lists were marked truncated. No new live requests used to diagnose the schema failures; exact parser cause remains unproven.
- Retained data: 954 separate quotes/itineraries (700 Skiplagged indicative, 254 swoop recent_search); 253 exact-segment itineraries and 701 insufficient-identity summaries. Every quote has extra_cost_unknown, seller/fare/baggage unknown; all swoop hidden_city=unknown, Skiplagged hidden_city=no from forced upstream exclusions. Zero repricing work items and zero exact-repriced offers. Safe-ranked view is correctly empty under current evidence requirements.
- Observed leads (returned snapshots only, no booking/total guarantee): Skiplagged Jan 1 at IDR 5,511,960 (original USD 305 × quoted rate 18,072; 23h40m, one stop, missing full legs). Swoop Jan 5 at IDR 5,751,400 (CGK–TPE–CTS, CI2764/CI130, 10h20m); Jan 6 same amount/duration with CI764/CI130. Jan 5 is IDR 239,440 above the lower indicative number, with a materially shorter observed itinerary, but taxes/fees/bags/seller confirmation still absent. Do not interpret this partial job as cheapest across the entire Dec–Feb range.
- UI findings: no browser page errors or 375px horizontal overflow; cancelled safe-empty view has no explanation/CTA despite retained advertised leads. Desktop header repeats price once unformatted (`5511960 IDR`) and again formatted. On mobile, no fare appears above the first 850px because cancellation, coverage and repeated warnings dominate. Job route/date/filter summary is missing; source errors/unpriced count are not exposed usefully (copy leaks `unpriced_candidate_count` implementation name). Airline/connection context is secondary or absent, and warnings repeat across cards.
- Suggested engineering priorities, not implemented by this assessment: (1) diagnose the 14 source-schema failures with sanitized targeted fixtures; (2) allow budgeted candidate checks during long scans and/or a server-owned user-triggered check so cancelled large jobs can still expose seller evidence; currently detailed scanning precedes verification; (3) preserve source airline names as non-identity summary metadata when supplied, without inventing legs/merging uncertain itineraries; (4) remove/disable/explain hidden-city inclusion control because this Skiplagged adapter always requests includeHiddenCity=false regardless of the query toggle, while swoop cannot classify it.
- Suggested P4.5 presentation priorities: explicit "954 advertised offers; 0 meet safe comparable criteria" state with advertised CTA; compact route/date/filter + 36/78 coverage summary; collapsible error details showing 14 swoop failures and 18 unpriced candidates in plain language; compact price/date/duration/connection/source rows; expandable repeated evidence; consistently formatted currency; distinguish retrieved time from actual price-checked time. A date-level cheapest summary should use backend Decimal/coverage semantics if added, not frontend money calculations or query pruning.
- No application code changed for this review. Do not weaken hidden-city/unknown-cost exclusions to populate the default view. Owner can use a narrow date window for faster end-to-end checking while engineering work is planned. P4.5 design brief remains the active handoff; changes above require implementation/validation before any completion claim.

## Provider feasibility evidence

Consolidated in full from the former standalone provider report at the owner's
request. P0 findings below are historical observations from 2026-11-09, followed
by the P3 production-adapter canary. The provider decision ledger above governs
current owner-accepted personal-use scope; earlier conditional/unresolved wording
is retained as historical evidence and does not reopen those decisions.

Evidence corrections already established during implementation: the P0 swoop
search contained 11 candidates, **10 priced and 1 unpriced**, despite the original
"11 priced" wording below. Production Skiplagged normalization conservatively
keeps even nonstop cards unmatched because operating-carrier identity is absent.

**Date:** 2026-11-09
**Route/date used for all live probes:** MEL → DPS, departing 2026-12-16, one-way, 1 adult, economy (the same non-live example fixture route named in `docs/README.md`). All prices below are real numbers returned by the providers at probe time — they are **not fabricated**, but they are a snapshot and must not be treated as current or bookable.
**Environment:** macOS, Python 3.12.16 (installed via Homebrew for this probe), `mcp` SDK 2.3.0, `swoop-flights` 0.7.0 (installed from PyPI into a throwaway venv `.venv_probe/`, not committed).
**Redacted fixtures:** `contracts/fixtures/provider/skiplagged_probe_*.json`, `contracts/fixtures/provider/swoop_probe_*.json`. Opaque `selector` and `booking_url` values were replaced with `<redacted-... len=N>` placeholders before committing, per `docs/07_TESTING_AND_OPERATIONS.md`'s evidence-retention rule. Raw unredacted responses were not persisted outside this session.
**Exact probe commands:**
```bash
source .venv_probe/bin/activate
python scripts/provider_probe_skiplagged.py            # tools/list only
python scripts/provider_probe_skiplagged.py --search --faq   # + 1 search call + 4 FAQ queries
python scripts/provider_probe_swoop.py                  # 1 search + 1 price_selector + 1 basic-economy search
```
Each probe script makes a small, fixed number of calls (no loops, no retries beyond library defaults) and was run once per variant in this session — low-volume by construction.

**Not performed in this session:** manual side-by-side comparison against the Skiplagged website or Google Flights in a browser. This environment has no browser/display available to the agent. This is a real gap in the P0 checklist (`docs/03`'s "attempt a low-cost comparison with the supplier/airline website") and should be done manually by the owner before relying on either provider for real money decisions. Treat the manual-comparison item below as **unverified**, not passed.

---

### Skiplagged remote MCP

**Endpoint:** `https://mcp.skiplagged.com/mcp` (no auth — confirmed, connected without credentials)
**Source:** https://skiplagged.github.io/mcp/ (docs), `skiplagged.com/terms` (site-wide terms)

#### Claims vs observed

| Claim (docs) | Observed (this session) |
|---|---|
| No authentication required | Confirmed — `ClientSession.initialize()` succeeded with no credentials. |
| Tools include flight/calendar/hotel/car search | `tools/list` returned exactly 10 tools: `sk_flights_search`, `sk_destinations_anywhere`, `sk_flex_departure_calendar`, `sk_flex_return_calendar`, `sk_hotels_search`, `sk_cars_search`, `sk_hotel_details`, `sk_faq_search`, `sk_resolve_location`, `sk_resolve_iata`. **No repricing/price-check/selector tool of any kind exists.** This is a hard fact, not an inference: repricing is not a Skiplagged MCP capability. `ProviderCapabilities.exact_reprice=False` for Skiplagged, confirmed. |
| Prices are approximate in non-USD currencies | Confirmed in output: `pricing.approximate=true`, `pricing.rate`, `pricing.rateAsOf`, and each flight's `price.usdAmount` (source-of-truth) alongside `price.amount` in the requested currency. Our domain layer must store `usdAmount` as the authoritative source amount and treat the IDR figure as a converted display value — matches `docs/03`'s FX-preservation rule. |
| Hidden-city fares included by default | Confirmed: `includeHiddenCity` input defaults to `true`. We can explicitly request `includeHiddenCity: false` (and `includeVirtualInterlining: false`) to exclude them at the query level — this is **better than assumed**: Skiplagged lets the caller opt out, so we don't have to post-filter unclassified candidates. Each `FlightCard.attributes` array also carries a classification tag (`"standard"`, `"nonstop"` observed, `"hidden-city"` not observed in this run because it was excluded by request — not confirmed what the exact string value is; needs one more probe call with `includeHiddenCity: true` before implementation, to pin the exact attribute string(s) used for hidden-city/self-transfer classification). |
| Site terms prohibit scraping, commercial use, redistribution | Confirmed via `skiplagged.com/terms`: explicit bans on "robot, spider, scraper or other automated means," any "commercial or non-personal purpose," and "distribute, transmit, display, ... re-sell any information ... obtained from this Site." **The MCP docs page does not restate or override these terms, and `sk_faq_search` queried 4 times for caching/aggregation/commercial/redistribution policy returned zero matching FAQ articles for 3 of 4 queries** — i.e., no explicit MCP-specific permission was found anywhere reachable in this session. |

#### Fields present / absent (for canonical domain mapping)

- **Present per result:** `airlines` (string, may be multi-carrier comma-joined — not itemized per segment), `departure`/`arrival` (airport + local ISO datetime with offset — only first-origin/last-destination, not per-leg), `duration`, `layovers` (count only), `price.{amount,currency,usdAmount}`, `deepLink` (public search URL + `#trip=<carrier><flightnum>` fragment, not a signed URL), `attributes` (string tags).
- **Absent:** no structured per-segment array (operating vs marketing carrier, individual flight numbers, intermediate airports) for itineraries with `layovers > 0`; no fare family/brand; no seller/OTA name; no baggage allowance; no `is_estimate`/`is_complete`/source-timestamp field in the output schema (only `pagination.totalAvailable/currentlyShowing` for truncation signal); no reprice/selector handle.
- **Consequence for `docs/03`'s matching algorithm:** nonstop Skiplagged results have just enough identity (single flight number embedded only in the `deepLink` fragment, not a typed field) to be a usable but weak `exact_segments` candidate; any itinerary with `layovers ≥ 1` lacks typed per-segment identity and **must** be treated as `insufficient_identity` under the conservative-matching rule — we cannot safely dedupe/merge connecting Skiplagged itineraries against another provider's segments.

#### Live sample (redacted selector/links kept short; full in fixture)

MEL→DPS 2026-12-16, 5 cheapest-by-value, `includeHiddenCity=false`, IDR: nonstop fares from Garuda Indonesia (IDR 4,907,458 / USD 271), Jetstar (×2), Malindo Air, TransNusa — see `contracts/fixtures/provider/skiplagged_probe_20261109T123430Z.json` for the full structured payload (`search_structured_content`).

#### Verdict: **CONDITIONAL GO**

Usable for a personal, low-volume, single-operator deployment: the MCP server is explicitly built and marketed for exactly this kind of AI-agent/no-auth consumption (`utm_medium=ai` tracking params are a strong signal of intended use), it is reachable with zero friction, and it returns real, usable flight data with an explicit hidden-city opt-out. **It is NOT cleared for redisplaying results to other users, caching beyond the duration of a single job, or any commercial use** — the main site's written terms prohibit exactly that, and nothing MCP-specific grants an exception. Concretely: `permitted_to_aggregate=unknown→treat as false for multi-user/public deployment`, `can_cache=short-TTL-only (job lifetime)`, `attribution_required=yes (per their own utm/branding pattern, keep deep links intact)`. Enable only as `enabled=true` in a **single-owner, non-redistributed, personal-use** configuration; do not enable for a publicly shared instance without written permission from Skiplagged. No exact-repricing capability exists — all Skiplagged offers are `recent_search` or `indicative` at best, never `repriced_exact`.

---

### swoop (reverse-engineered Google Flights RPC)

**Package:** `swoop-flights` 0.7.0 (PyPI), MIT license
**Source:** https://github.com/saraswatayu/swoop

#### Claims vs observed

| Claim (README) | Observed (this session) |
|---|---|
| Real prices, no API key | Confirmed: `swoop.search("MEL","DPS","2026-12-16", cabin="economy", include_basic_economy=False)` returned 11 priced `TripOption`s with `is_complete=True`, no credentials needed. |
| `price_selector()` gives exact fare + booking options | Confirmed: took the top result's `selector`, called `price_selector()`, got `PriceResult` with `price=7,764,811 IDR`, `is_estimate=True`, `is_basic_economy=False`, and 1+ `booking_options` entries with `seller_name="Jetabroad"`, `fare_family="basic"`, `is_basic=True`, `rebookability_signal="restricted"`, and a Google-redirect `booking_url`. **Important nuance confirmed live:** the top-level `PriceResult.is_basic_economy` can disagree with an individual `booking_options[i].is_basic` — the top-level field describes the priced itinerary/selector as requested, while each booking option is its own seller/fare combination. Our matching layer must key offers off `booking_options[]`, not assume the top-level flag applies to every seller shown. |
| Full segment-level itinerary detail | Confirmed and **materially richer than Skiplagged**: each `TripOption.legs[].itinerary.segments[]` has `airline`, `flight_number`, `operator` (separate marketing/operating field, empty string observed = same-carrier operated), `aircraft`, per-segment local departure/arrival date+time, `travel_time`, amenities, `co2_grams`. This satisfies `docs/03`'s itinerary-identity requirement (ordered segments with flight numbers) for both nonstop and connecting itineraries — unlike Skiplagged. |
| `include_basic_economy` toggle changes results | Confirmed: with the flag off, cheapest observed was ~7.76M IDR (from the selector probed); with it on, `cheapest_price=4,891,694 IDR` across the same 11-result response (`is_complete=True` both times) — a materially lower floor, as expected. |
| Hidden-city detection | **Not present anywhere in the library.** No field, no flag, no mention in README or observed output. We cannot get a hidden-city signal from swoop; every swoop offer must be recorded `hidden_city=unknown` (not `no`) per the three-valued enum rule, unless we later add independent detection logic. In practice Google Flights itself does not typically sell overt hidden-city fares the way Skiplagged does, which lowers — but does not eliminate — the practical risk; this is an assumption, not a proof. |
| Google rate-limits aggressively; use conservative retries | Not stress-tested (by design — no intentional rate-limit probing). 3 live calls (search ×2, price_selector ×1) in this session all succeeded on first attempt with no 429s. |

#### Legal/compliance note (the real risk for swoop)

The `swoop-flights` package itself is MIT-licensed with no usage restriction on the code. The risk is **not** the library's license — it's that the library calls Google's undocumented, internal `FlightsFrontendService` RPC with TLS fingerprint impersonation to look like a browser, which is the kind of automated access Google's general Terms of Service typically restrict for unauthorized clients (standard clause across Google products; this session did not fetch and quote Google's specific Flights ToS text, so treat this as a known category of risk, not a verified quote). This is a materially different risk profile than Skiplagged's MCP server, which is a product Skiplagged built and published *for* this kind of use. swoop's README itself only disclaims "not affiliated with Google" and warns the RPC "can change without notice" — it does not claim legal clearance.

#### Verdict: **CONDITIONAL GO**

Functionally the stronger provider — full segment identity, basic-economy toggle, seller-level booking options, and an actual (if estimate-flagged) repricing call via `price_selector()`/`check_price()`. Enable for low-volume personal use (`enabled=true`, bounded executor, 1–2 concurrent calls, generous backoff per the README's own guidance) with `exact_reprice` capability wired to `price_selector`, but mark **`price_status` from swoop as `repriced_exact` only when `is_estimate=False`** — the single live call in this session returned `is_estimate=True`, so even "repriced" swoop quotes default to a lower-confidence label until proven otherwise on a given itinerary. Legal risk (unauthorized automated access to Google's internal RPC) is real and unresolved by this probe; it is a judgment call for the owner whether to accept that risk for a personal/low-volume tool — flagging per `docs/06`'s escalation rule rather than deciding unilaterally that it's fine.

---

### Combined P0 gate outcome

**At least one provider (both, conditionally) exposes a usable, real, low-volume-compliant one-way search for the target route/date class.** Gate passed — proceed to P1 (domain + fake-provider slice) is unblocked. Neither provider reaches an unconditional GO:

| Provider | Verdict | Condition for wider/public use |
|---|---|---|
| Skiplagged MCP | **GO** — personal/single-owner use (owner-accepted 2026-11-09) | Site terms ban commercial use/redistribution/scraping; no MCP-specific permission found. Must revisit (seek written permission) before any public/multi-user launch. |
| swoop | **GO** — personal/low-volume use (owner-accepted 2026-11-09) | Legal status of unauthorized Google RPC access remains unresolved in the abstract; owner explicitly accepted this risk for a personal project. Must revisit if this ever scales or becomes commercial. |

#### Owner decisions (resolved 2026-11-09, per `docs/06` stop/escalation rule)

These were flagged as fundamental-incompatibility-style questions rather than resolved unilaterally. Owner's answers:

1. **Skiplagged, personal/non-redistributed use despite the site-wide commercial/redistribution ban:** accepted, conditioned on the project staying personal/non-redistributed. Confirmed understanding: fine to run for yourself (and people you personally let use it), not fine to turn into a public signup product without separately asking Skiplagged.
2. **swoop's reliance on undocumented Google RPC access:** accepted for a personal, low-volume project after the legal-risk tradeoff was explained (contract-violation / blocking risk, not realistic legal-action risk at hobby scale). Revisit before any scale-up or commercialization.

Both acceptances are personal-project-scoped. `provider_registry.permitted_to_aggregate` and `can_cache` should still default to the conservative personal-use settings described per-provider above — the owner's acceptance is not a blanket "treat as a licensed commercial API."

#### Follow-up probe items

- Ran one additional `sk_flights_search` call with `includeHiddenCity: true, includeVirtualInterlining: true, limit: 15` for MEL→DPS 2026-12-16 to pin the exact hidden-city `attributes` tag string. **Inconclusive**: the only tags observed across all 15 results were `"standard"`, `"nonstop"`, `"one-stop"` — no hidden-city or virtual-interlining fare happened to rank in the top 15 for this specific route/date, so the exact tag string for those classifications is still unconfirmed. Needs a route/date known to surface a cheap hidden-city fare (not guessed/fabricated here) before the adapter can safely map `attributes` to our `hidden_city` enum; until then, treat any Skiplagged result as `hidden_city=unknown` whenever `includeHiddenCity=true` is used, and only trust `hidden_city=no` when the query itself was sent with `includeHiddenCity=false` (as in the main probe above).
- Manual browser-based price comparison against skiplagged.com and Google Flights for the same route/date — still not performed (no browser available to the agent in this session).

---

### P3 live canary (2026-11-09, addendum)

Where the P0 section above called the SDKs/MCP server directly with ad hoc
scripts, this canary runs the **actual production adapter classes**
(`cheapwings.providers.skiplagged.SkiplaggedProvider`,
`cheapwings.providers.swoop.SwoopProvider`) against live endpoints — the
real normalization/error-handling code path the worker uses, not a probe
shim. Same route/date as P0 (MEL→DPS, 2026-12-16) for comparability.
`mcp`==2.3.0, `swoop-flights`==0.7.0, `airportsdata`==20261103 (the pinned
`backend[live]` extra). One search call per provider, one `reprice()` call
on swoop's top result — still low-volume, still a single run.

**Command:** `python scripts/p3_live_canary.py` (script redacts nothing by
itself — its raw JSON output contains swoop's opaque selector and was
**not committed**; only this redacted summary is kept).

**Skiplagged:** `SkiplaggedProvider.search()` returned 20 normalized offers,
status `succeeded_results`, no adapter exceptions. Sample offer: original
USD 272 → comparable IDR 4,925,566 via a preserved `FXSnapshot` (rate
18108.7, matches the live rate at probe time), `hidden_city=no` (query sent
`includeHiddenCity=false`), `checked_bag=unknown`, `price_status=indicative`,
`is_estimate=True`, link correctly scoped to `generic_search` and validated
`https://skiplagged.com/...`. No fabricated seller/fare-family — both
`null` since the source never provides them, exactly per the P0 findings.

**swoop:** `SwoopProvider.search()` returned 10 priced + **1 unpriced**
candidate — the adapter's explicit `unpriced_candidate_count` correctly
caught the same no-price/no-currency quirk documented in the P0 section,
on a fresh live call, not just the frozen fixture. `SwoopProvider.reprice()`
on the top result succeeded: real seller `"Jetstar"`, `is_estimate=False`,
opaque `provider_quote_handle` populated (never a link — swoop reprice
offers don't expose a direct URL). `exact_product_match=False` here because
the *search*-stage offer never carries seller/fare_family (swoop doesn't
expose that pre-reprice), so the adapter's independent-field match
intentionally cannot succeed from a bare search→reprice chain with no
in-between verification step — this is the conservative behavior
`docs/03`'s matching rule requires, not a bug.

**Verdict:** both adapters behave correctly against live data, consistent
with the P0 findings and the existing offline test suite (which replays
these same P0 fixtures through the identical adapter code in
`backend/tests/integration/test_p3.py::test_recorded_real_adapters_api_summary_fx_and_expiry`).
No new GO/NO-GO decision needed — this confirms the already-accepted
personal-use GO for both providers extends to the real adapter
implementation, not just the raw SDK.

### Reporting consolidation (2026-11-09)
- Owner explicitly required all reports to live in WORK_LOG.md. Merged the complete P0 provider evidence and P3 canary addendum here, removed the standalone report, and updated active specifications, bootstrap instructions, README links and the canary docstring. No provider calls or application behavior changes.
- Updated P4.5 handoff instructions: the UI/UX agent must append its design-return findings here rather than create another report. Release and test summaries likewise belong here. Static UI/UX prompts/integration specifications remain separate assignment artifacts, as requested previously. Historical V4 reference left untouched.

## P4.5 handover task — ready for UI/UX agent

- Branch: `p4.5-ui-ux-handoff`; base main commit: `532f080`. Work only on the designated branch or a focused child branch, never directly on main. Prefer an isolated checkout so the owner's currently running live test is not hot-reloaded by design edits. Do not copy local `.env`, live DBs, credentials or raw live quote payloads into that checkout.
- Read order: this WORK_LOG first, then `docs/P4_5_UI_UX_AGENT_PROMPT.md`, `docs/P4_5_UI_UX_INTEGRATION.md`, active product/UI specs, and actual React components/API types. All findings and design-return notes stay in WORK_LOG.md; no separate report files.
- Deliver actual focused React/CSS changes with a component/prop migration map where needed. Retain existing request client/hooks, server ranking, monetary strings and source-local time helpers; no backend/API/provider policy changes. Static screenshots alone do not satisfy this assignment.

Presentation task checklist, grounded in the owner's live-result review:

- [ ] Show a compact route, inclusive date range and requested-filter summary when viewing an existing job.
- [ ] Explain an empty safe-ranked view in every terminal state, including cancellation: no offer currently meets the safe/comparable criteria. Keep an explicit advertised-results CTA available without changing the default ranking or inventing eligibility.
- [ ] Make progress/source coverage and cancellation concise on mobile; show plain-language source failures and unpriced counts. Move repeated technical detail behind accessible disclosure while keeping important price/risk/coverage caveats visible.
- [ ] Improve comparison rows/cards: consistently formatted price, date/time with source offset, stops/duration, known connection/carrier codes, source/confidence and distinct seller offers. Never invent airline names, legs, baggage or sellers when metadata is absent.
- [ ] Preserve attribution, original/converted currency and FX evidence. Distinguish retrieval time from an actual same-offer price check. Avoid implying that checked bags were requested when the user's filter says otherwise.
- [ ] Retain responsive form, runtime auth input, URL job recovery, stale-response protection, pagination, retry, cancellation and safe external-link handling. Use existing synthetic browser fixtures or isolated fake services for QA.
- [ ] Verify 375/768/1440, keyboard focus and enlarged text; run `npm test`, `npm run build`, and `npm run test:browser` from `apps/web`. Run backend tests from root before final integration. Append actual commands/results, screenshot paths, design rationale, changed files and remaining issues here.

Explicitly outside the designer's scope: the 14 swoop schema failures, incremental repricing scheduling, exposing additional upstream airline summary fields, and provider-side hidden-city query behavior. These are engineering follow-ups requiring separate implementation/evidence; do not conceal them with UI labels or fabricated data.

Acceptance/integration: implementation agent reviews the patch against the base SHA, preserves newer functional work, validates with fake/intercepted data, and records P4.5 acceptance here before merging. No public deployment, unrequested main push or native-iOS replacement. P5 starts after P4.5 integration and requires full Xcode for build/simulator acceptance.

### P4.5 handover preparation validation (2026-11-09)
- Confirmed the complete original provider-report body (including the P3 canary addendum) is preserved in WORK_LOG.md with nested headings. Removed standalone report and all active references/instructions to separate provider, release or design-return report files. Historical V4 untouched.
- `.venv/bin/python -m pytest backend/tests -q` → **85 passed**. `git diff --check` passed. Documentation consolidation and canary docstring only; no application behavior changes or live provider calls.
- Dedicated handover branch created from `532f080`; live services left running. Prepared focused commit for publication to `origin/p4.5-ui-ux-handoff`. Next agent starts with the P4.5 handover task checklist above and appends its actual return findings here.
