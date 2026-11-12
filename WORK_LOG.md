# WORK_LOG.md — Current State (keep under ~80 lines)

Source of truth for **current** phase status, approvals, and the exact next task. History and long evidence live in [`docs/log/`](docs/log/) (read only when a task needs it). Do not create other report files elsewhere.

## Rules for editing this file
- Keep this file under ~80 lines. Latest checkpoint: at most five short bullets; replace old status instead of appending.
- Put benchmark tables, timings, architecture reasoning and detailed test results in `docs/log/<phase>.md`; root updates contain only status, approvals, blockers and evidence links.
- At phase close: collapse its detail into `docs/log/`, leave one tracker row. Replace (don't append to) "Latest checkpoint" and "Next task".

## Project basics
- Repo `farhaniqbalta/CheapWings`, current branch `main`, including P4.11 merge `4c98386`, personal single-owner use. Python 3.12 backend (`backend/src/cheapwings`), React web (`apps/web`), SQLite + Alembic. Native iOS (P5) needs full Xcode (only CLT present).
- Owner merges PRs; never merge/push automatically. Confirm before toolchain installs or live provider probes.
- Baseline/environment history: [baseline-and-old-summary](docs/log/baseline-and-old-summary.md).

## Phase tracker
| Phase | Status | Evidence / log |
|---|---|---|
| P0 Provider feasibility | Done; owner-accepted personal-use GO | [provider-feasibility-evidence](docs/log/provider-feasibility-evidence.md) |
| P1 Domain + fake provider | Done | 42 tests; [p2-p4](docs/log/p2-p4.md) |
| P2 Durable jobs + API | Done | 72 tests, OpenAPI, runbook; [p2-p4](docs/log/p2-p4.md) |
| P3 Real providers + repricing | Done (offline + live canary); real sources opt-in via `ENABLED_PROVIDERS` | [p2-p4](docs/log/p2-p4.md) |
| P4 React web | Done | [p2-p4](docs/log/p2-p4.md) |
| P4.5 UI/UX refinement | Done; merged d9f5e77 | [p4.5](docs/log/p4.5.md) |
| Provider/cache + OctoTrip | Done; merged 37a536b; source picker added in P4.7 | [research-cache-p4.6-p4.7](docs/log/research-cache-p4.6-p4.7.md) |
| P4.6 Web UI update | Done; PR #1 merged 32190a1 | same file |
| P4.7 Source controls + historical lifecycle | Done; PR #2 merged 229fa3f; 126 backend / 4 web / 65 browser checks | same file |
| P4.8 Provider intervals + staggered scheduling | Experiments complete; scheduling delivered through P4.9 | [interval review](docs/log/p4.8.md), [throughput experiment](docs/log/p4.8-throughput-experiment.md) |
| P4.9 Scheduler architecture | Done; PR #3 merged a932900; Google Flights transport restoration deferred | [P4.9 review and implementation](docs/log/p4.9.md) |
| P4.10 Smart locations | Done; PR #4 merged `9a160d9` | [P4.10 implementation](docs/log/p4.10.md) |
| P4.11 Fli provider | Done; owner-accepted; [PR #5](https://github.com/farhaniqbalta/CheapWings/pull/5) merged `4c98386` | [P4.11 implementation and verification](docs/log/p4.11.md) |
| P4.12 Shared global pool | Implemented + offline-verified on branch `p4.12-global-pool`; awaiting owner review (not pushed) | [P4.12 review, benchmark and risks](docs/log/p4.12.md) |
| P5 SwiftUI native iOS | Not started; needs full Xcode | |
| P6 Release acceptance | Not started | |

## Provider decision ledger
| Provider | Decision | Key limits (details in provider-feasibility-evidence / research logs) |
|---|---|---|
| Skiplagged MCP | GO, personal use only (owner 2026-11-09) | Terms ban commercial/redistribution; revisit before any public launch. No exact reprice; no per-segment identity for connections; hidden-city tag unconfirmed. |
| swoop | GO, personal/low-volume (owner 2026-11-09) | Undocumented Google RPC, ToS risk accepted; no hidden-city signal; price often an estimate; key offers off `booking_options`. |
| OctoTrip | GO, opt-in personal use (owner 2026-11-10) | Indicative only, no exact reprice, cache disabled; fare/fees/risk/source-age unknown; 900s lifecycle; nearby airports filtered. |
| Fli | Owner-requested personal-use integration (2026-11-12) | Google Flights public page; indicative quotes/search links; basic-economy exclusion unsupported; same inventory as swoop. |

## Latest checkpoint
- P4.12 on branch `p4.12-global-pool` (from `5e7f865`): per-provider concurrency ceilings removed; one shared global pool `WORKER_MAX_IN_FLIGHT` (default 9, now 1..100) with unchanged start intervals, cooldowns, Retry-After, leases and fencing. `<PROVIDER>_CONCURRENCY` removed from code, `.env` and `.env.example`.
- Adapter-intrinsic thread pools stay as adapter limits only: Fli pool = G (lazy threads), obsolete swoop fixed 3.
- Verification: 269 passed / 11 skipped (main 264); 5 new pool tests fail on P4.9 and pass on P4.12. No live provider traffic.
- Synthetic benchmark (15 min per variant): slot-bound completion 30–86% faster at equal G; pacing-bound unchanged; a late job behind a pool-filling slow provider waits for one slow call at G9/16. G100 is limited by pre-existing `finish`/`finalize` persistence cost, not scheduling. [Details](docs/log/p4.12.md).

## Next task
Owner review of P4.12: decide on the pool-monopolization mitigation, production G and local OctoTrip interval, any live validation, and PR publication. Do not push or merge without approval.

## Deviation log (approved design changes)
| Date | Change | Reason | Owner decision? |
|---|---|---|---|
| 2026-11-09 | Canonical itinerary gets explicit incomplete summary + nullable offer metadata/FX evidence | Skiplagged connections lack segments; swoop needs timezone reference; never fabricate | No (within spec) |
| 2026-11-09 | Add P4.5 UI/UX refinement phase | Owner requested | Authorized |
| 2026-11-09 | Polling-hook repair in P4.5 | Same-search refresh unmounted cards | No (corrective) |
| 2026-11-10 | Itinerary supports observed airport-change transfers + carrier display metadata | NRT→HND transfer rolled back a date; undeclared gaps stay invalid | No (corrective) |
| 2026-11-10 | Observation expiry separate from job budget; expired metadata returned with HTTP 200 | Owner-approved retention exception | Approved |

Full pre-restructure text of every section above: [baseline-and-old-summary](docs/log/baseline-and-old-summary.md).
