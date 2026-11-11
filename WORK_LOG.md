# WORK_LOG.md — Current State (keep under ~80 lines)

Source of truth for **current** phase status, approvals, and the exact next task. History and long evidence live in [`docs/log/`](docs/log/) (read only when a task needs it). Do not create other report files elsewhere.

## Rules for editing this file
- Keep this file under ~80 lines. Latest checkpoint: at most five short bullets; replace old status instead of appending.
- Put benchmark tables, timings, architecture reasoning and detailed test results in `docs/log/<phase>.md`; root updates contain only status, approvals, blockers and evidence links.
- At phase close: collapse its detail into `docs/log/`, leave one tracker row. Replace (don't append to) "Latest checkpoint" and "Next task".

## Project basics
- Repo `farhaniqbalta/CheapWings`, review branch `p4.9-scheduler-review` from `5d72be4`, personal single-owner use. Python 3.12 backend (`backend/src/cheapwings`), React web (`apps/web`), SQLite + Alembic. Native iOS (P5) needs full Xcode (only CLT present).
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
| P4.9 Scheduler architecture | Option A implemented; offline verification passed; owner requested C3 defaults | [P4.9 review and implementation](docs/log/p4.9.md) |
| P5 SwiftUI native iOS | Not started; needs full Xcode | |
| P6 Release acceptance | Not started | |

## Provider decision ledger
| Provider | Decision | Key limits (details in provider-feasibility-evidence / research logs) |
|---|---|---|
| Skiplagged MCP | GO, personal use only (owner 2026-11-09) | Terms ban commercial/redistribution; revisit before any public launch. No exact reprice; no per-segment identity for connections; hidden-city tag unconfirmed. |
| swoop | GO, personal/low-volume (owner 2026-11-09) | Undocumented Google RPC, ToS risk accepted; no hidden-city signal; price often an estimate; key offers off `booking_options`. |
| OctoTrip | GO, opt-in personal use (owner 2026-11-10) | Indicative only, no exact reprice, cache disabled; fare/fees/risk/source-age unknown; 900s lifecycle; nearby airports filtered. |

## Latest checkpoint
- Corrected Skiplagged HTTP 429 detection to preserve Retry-After through MCP wrapping; raised its default/local interval to 3s (C3 retained).
- Coverage dropdown now shows queued, running and retry-wait source work while jobs are active.
- Existing API/web services remain available for owner testing; restart the durable worker to load the fix.
- Prior offline verification and P4.9 evidence: [scheduler log](docs/log/p4.9.md); merge remains owner-controlled.

## Next task
Restart the local worker and review the provider cooldown behavior and progress dropdown at http://localhost:5173; then review the P4.9 PR. P5 still needs full Xcode.

## Deviation log (approved design changes)
| Date | Change | Reason | Owner decision? |
|---|---|---|---|
| 2026-11-09 | Canonical itinerary gets explicit incomplete summary + nullable offer metadata/FX evidence | Skiplagged connections lack segments; swoop needs timezone reference; never fabricate | No (within spec) |
| 2026-11-09 | Add P4.5 UI/UX refinement phase | Owner requested | Authorized |
| 2026-11-09 | Polling-hook repair in P4.5 | Same-search refresh unmounted cards | No (corrective) |
| 2026-11-10 | Itinerary supports observed airport-change transfers + carrier display metadata | NRT→HND transfer rolled back a date; undeclared gaps stay invalid | No (corrective) |
| 2026-11-10 | Observation expiry separate from job budget; expired metadata returned with HTTP 200 | Owner-approved retention exception | Approved |

Full pre-restructure text of every section above: [baseline-and-old-summary](docs/log/baseline-and-old-summary.md).
