# WORK_LOG.md — Worker Progress Tracker

This file is the source of truth for current phase status, implementation decisions, provider approvals, validation evidence, blockers, and the exact next task. Checkpoint entries below are historical; use the phase tracker and latest checkpoint summary for current status.

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
| P0 Provider feasibility | Done (owner-accepted personal-use GO both providers) | `docs/PROVIDER_POC_REPORT.md`; redacted fixtures in `contracts/fixtures/provider/`; `scripts/provider_probe_skiplagged.py`, `scripts/provider_probe_swoop.py` | None for accepted personal scope; revisit before public/commercial use | P3 adapter integration |
| P1 Domain + fake provider | Done | `backend/src/cheapwings/{domain,engine,providers}`, 42 passing tests, `python -m cheapwings.cli_demo` offline demo | None | Start P2 — SQLite persistence, durable scheduler, REST API |
| P2 Durable jobs + API | Implemented; final process acceptance pending | 72 passing tests, migrations/no schema drift, OpenAPI, runbook | Sandbox denies localhost socket bind and .git writes | Run process smoke and commit in unrestricted terminal; then P3 |
| P3 Real providers + repricing | Not started | | | |
| P4 React web | Not started | | | |
| P5 SwiftUI native iOS | Not started | | | Full Xcode required, only CLT present |
| P6 Release acceptance | Not started | | | |

## Provider decision ledger
| Provider | GO/CONDITIONAL GO/NO-GO | Permission/terms | Tested version + date | Missing fields/risks |
|---|---|---|---|---|
| Skiplagged MCP | **GO (personal/single-owner use)** — owner accepted 2026-11-09 | Site terms (`skiplagged.com/terms`) ban commercial use/redistribution/scraping; `sk_faq_search` found no MCP-specific permission. Owner explicitly confirmed: acceptable as long as the project stays personal/non-redistributed; revisit (seek written permission) before any public/multi-user launch. | `mcp` SDK 2.3.0, probed 2026-11-09 | No exact-reprice tool exists at all (10 tools listed, none is repricing). No per-segment flight-number data for connecting itineraries (`layovers≥1` → `insufficient_identity`). No fare brand/seller/baggage fields. Hidden-city `attributes` tag string still unconfirmed (no hidden-city fare surfaced in the probed route/date even with `includeHiddenCity=true`). |
| swoop | **GO (personal/low-volume use)** — owner accepted 2026-11-09 | MIT-licensed library, but calls Google's undocumented internal RPC with browser TLS impersonation — standard Google ToS risk for unauthorized automated access (contract-violation risk, not verified-quote; realistic consequence is blocking/breakage, not legal action, at hobby volume). Owner explicitly accepted this risk for a personal project. Revisit if this ever scales/commercializes. | `swoop-flights` 0.7.0, probed 2026-11-09 | No hidden-city signal at all (`hidden_city` must always be `unknown` for swoop offers). `price_selector()` returned `is_estimate=True` on the one live call — can't assume `repriced_exact` without further testing on more itineraries. Top-level `is_basic_economy` can disagree with individual `booking_options[].is_basic` — must key offers off `booking_options`, not the top-level flag. |

## Latest checkpoint summary
- Phase: P2 implementation complete; gate remains **pending process-level acceptance and commits** because of sandbox restrictions. Do not repeat P0/P1 or assume process smoke passed.
- Files: SQLAlchemy storage/models/repository, two versioned Alembic migrations/config; application worker/projections/typed contracts; REST routes/main/settings; adapter registry; separate worker executable; 30 integration tests; OpenAPI contract/exporter; `.env.example`, root README, P2 implementation decisions consolidated in this work log, process smoke script.
- Tests/commands: `.venv/bin/python -m pytest backend/tests -q` → **72 passed** (42 original + 30 P2), one upstream Starlette/httpx deprecation warning. Ruff check on all new P2 Python passes. `alembic upgrade head` and `alembic check` → no schema drift. Original `python -m cheapwings.cli_demo` runs unchanged, 27 combinations/54 items/partial source failure with visibly synthetic prices.
- Functional evidence: API → SQLite → worker → partial results; accurate unique coverage; distinct offers; decimal strings; pagination snapshot remains stable even as more work completes; restart preserves completed work; lease fencing rejects stale completions; transaction rollback preserves queue consistency; Retry-After survives restart; shared concurrency holds even during cancellation; removed sources become explicit skipped entries; bearer auth and atomic owner quotas enforced.
- P1 domain/engine/fake adapter files unchanged (confirmed with git diff). Provider approvals remain accepted for personal scope. No real provider calls made or live adapters enabled.
- Environment restrictions: `git add`/`git commit` failed creating `.git/index.lock` (Operation not permitted). `scripts/p2_smoke.py` failed at localhost socket bind (PermissionError). No commits created; changes are in the working tree, including new untracked files. These are sandbox denials, not application test failures. Do not claim full process acceptance.
- Next smallest task: in an unrestricted terminal, run `.venv/bin/python scripts/p2_smoke.py`, then stage/commit the P2 work (proposed messages below), update this tracker to P2 Done if smoke passes, then begin P3 per docs/06. Do not delete/reinitialize .git or repeat provider permissions.

## Explicit deviation log
| Date | Approved design changed | Reason/evidence | Owner decision needed? |
|---|---|---|---|

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
