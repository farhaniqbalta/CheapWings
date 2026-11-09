# WORK_LOG.md — Worker Progress Tracker

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
| P0 Provider feasibility | Done (CONDITIONAL GO both providers) | `docs/PROVIDER_POC_REPORT.md`; redacted fixtures in `contracts/fixtures/provider/`; `scripts/provider_probe_skiplagged.py`, `scripts/provider_probe_swoop.py` | Neither provider has unconditional legal/terms clearance — owner decision needed (see report) | Owner decides on Skiplagged personal-use interpretation + swoop legal risk acceptance, then start P1 |
| P1 Domain + fake provider | Done | `backend/src/cheapwings/{domain,engine,providers}`, 42 passing tests, `python -m cheapwings.cli_demo` offline demo | None | Start P2 — SQLite persistence, durable scheduler, REST API |
| P2 Durable jobs + API | Not started | | | |
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
- Phase: P1 — pure-domain models + fake-provider offline vertical slice (complete) → starting P2
- Files changed: `backend/pyproject.toml` (new); `backend/src/cheapwings/domain/{money,segments,itinerary,offer,query,coverage}.py` (new); `backend/src/cheapwings/engine/{expansion,matching,ranking}.py` (new); `backend/src/cheapwings/providers/{base,fake}.py` (new); `backend/src/cheapwings/cli_demo.py` (new); `backend/tests/unit/test_*.py` (8 files, new); root `.venv/` created (gitignored, Python 3.12.16, editable install of `backend[dev]`)
- Tests/commands/results: `cd backend && python -m pytest -q` → **42 passed**. `ruff check src tests` → 5 cosmetic nits left unfixed (unsafe-fix-only `dict()`-to-literal suggestions), no correctness issues. `python -m cheapwings.cli_demo` from repo root runs the full offline pipeline: 27 route-date combos (1×3×9, matches the fixture example), 2 fake providers × 27 combos = 54 work items with 1 scripted failure + 1 scripted empty proving partial-coverage honesty, 27 matched itinerary groups, both `best_checked_deal` and `lowest_advertised` rankings printed with an explicit synthetic-fixture warning on every line.
- Demo evidence: CLI output above; test suite covers Money/Decimal correctness (float rejected, IDR zero-minor-units, FX conversion), query validation (rejects round-trip/multi-adult/same-origin-dest/reversed-dates/excess-combinations), itinerary identity (TZ-aware segments required, connected-segment check, fingerprint equality/inequality), conservative matching (same itinerary from 2 providers groups with distinct offers; different connections stay separate; duplicate quote_id is idempotent; insufficient-identity itineraries never merge), ranking (repriced_exact outranks cheaper recent_search; hidden_city yes/unknown excluded from default ranking; missing-baggage-cost excluded; Offer constructor itself rejects repriced_exact+is_estimate and repriced_exact+hidden_city combinations), and the fake provider (deterministic prices, synthetic-label on every seller, basic-economy toggle respected, scripted failure vs scripted empty are distinct, IDR amounts have zero minor units).
- Assumptions and warnings: `FakeProvider`'s synthetic prices are not magnitude-realistic (small IDR figures) — acceptable since it exists to prove pipeline correctness, not resemble real fares; every price is labeled `SYNTHETIC-FIXTURE-NOT-A-REAL-FARE`. `api/`, `application/`, `storage/` layers are intentionally not built yet (P2 scope).
- Next smallest task: begin P2 — SQLAlchemy models/Alembic migrations, durable job/work-item scheduler, REST v1 (`health`, `capabilities`, `POST searches`, `GET job`, `GET results`, `cancel`), wired to the P1 domain/engine/fake-provider code with no changes to domain logic

## Explicit deviation log
| Date | Approved design changed | Reason/evidence | Owner decision needed? |
|---|---|---|---|
