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
| P1 Domain + fake provider | Not started | | | Pure-domain models, `expand_routes_and_dates()`, fake providers, matching/ranking — no network |
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
- Phase: P0 — provider feasibility probing + owner risk acceptance (complete) → starting P1
- Files changed: `scripts/provider_probe_skiplagged.py`, `scripts/provider_probe_swoop.py` (new), `contracts/fixtures/provider/*.json` (4 redacted fixtures), `docs/PROVIDER_POC_REPORT.md` (new), `.gitignore` (new), this file
- Tests/commands/results: see exact commands in `docs/PROVIDER_POC_REPORT.md`. Skiplagged: `tools/list` (10 tools, 0 errors) + 1 real search call (5 nonstop MEL→DPS fares, real IDR/USD prices) + 4 FAQ policy queries + 1 follow-up hidden-city-tag probe. swoop: 1 `search()` (11 results, `is_complete=True`) + 1 `price_selector()` (real seller/fare data) + 1 basic-economy comparison search. All live calls succeeded on first attempt, 0 retries, 0 rate-limit errors.
- Demo evidence: redacted JSON fixtures in `contracts/fixtures/provider/`; narrative summary in `docs/PROVIDER_POC_REPORT.md`
- Assumptions and warnings: manual browser price comparison NOT performed (no browser available to the agent) — flagged as unverified, not skipped silently. Hidden-city `attributes` tag string for Skiplagged still unconfirmed. Google ToS risk for swoop stated as a known risk category, not a verified quote; owner accepted it explicitly for personal use.
- Next smallest task: begin P1 — pure-domain models + `expand_routes_and_dates()` + fake providers, offline, no network

## Explicit deviation log
| Date | Approved design changed | Reason/evidence | Owner decision needed? |
|---|---|---|---|
