# WORK_LOG.md — Current State (keep under ~80 lines)

Source of truth for **current** phase status, approvals, and the exact next task. History and long evidence live in [`docs/log/`](docs/log/) (read only when a task needs it). Do not create other report files elsewhere.

## Rules for editing this file
- Keep this file under ~80 lines. Latest checkpoint: at most five short bullets; replace old status instead of appending.
- Put benchmark tables, timings, architecture reasoning and detailed test results in `docs/log/<phase>.md`; root updates contain only status, approvals, blockers and evidence links.
- At phase close: collapse its detail into `docs/log/`, leave one tracker row. Replace (don't append to) "Latest checkpoint" and "Next task".

## Project basics
- Repo `farhaniqbalta/CheapWings`, current branch `main`, including P4.11 merge `4c98386`, personal single-owner use. Python 3.12 backend (`backend/src/cheapwings`), React web (`apps/web`), SQLite + Alembic. Native iPad (P5): Xcode 27.1 + Rust 1.100 installed; free Personal Team signing (3-app device limit).
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
| P4.12 Shared global pool | Done; [PR #7](https://github.com/farhaniqbalta/CheapWings/pull/7) merged `00c2fbb` | [P4.12 review, benchmark and risks](docs/log/p4.12.md) |
| P4.13 Persistence cost | Done; [PR #8](https://github.com/farhaniqbalta/CheapWings/pull/8) merged `984cfd2` | [P4.13 follow-up](docs/log/p4.12.md#p413-follow-up--result-persistence-cost-2026-11-13-branch-p413-finish-persistence) |
| P5.05/P5.06 Native iPad feasibility + spikes | Done; [PR #9](https://github.com/farhaniqbalta/CheapWings/pull/9) merged `ce7b343` | [P5.05 analysis](docs/log/p5.05.md), [P5.06 spikes](docs/log/p5.06.md) |
| P5.1 Shared Rust core | Done; [PR #10](https://github.com/farhaniqbalta/CheapWings/pull/10) merged `26dfc95` | [P5.1](docs/log/p5.1.md), [plan](docs/log/p5.1-plan.md) |
| P5.2 iPad app shell | Done; [PR #11](https://github.com/farhaniqbalta/CheapWings/pull/11) + follow-up [#12](https://github.com/farhaniqbalta/CheapWings/pull/12) merged `53c0f6c` | [P5.2](docs/log/p5.2.md), [plan](docs/log/p5.2-plan.md) |
| P5.3 Persistence + resume | Done; [PR #13](https://github.com/farhaniqbalta/CheapWings/pull/13) merged `6c431e9` | [P5.3](docs/log/p5.3.md), [plan](docs/log/p5.3-plan.md) |
| P5.5 iPad feature parity | Done; [PR #14](https://github.com/farhaniqbalta/CheapWings/pull/14) merged `3c38427`; Fli 0.25 s + P7 docs via [PR #15](https://github.com/farhaniqbalta/CheapWings/pull/15) | [P5.5](docs/log/p5.5.md), [plan](docs/log/p5.5-plan.md), [Fli 0.25 s test](docs/log/p5.5-fli-interval.md) |
| P5.6 iPad polish | Done; [PR #16](https://github.com/farhaniqbalta/CheapWings/pull/16) merged `addc272` | [P5.6](docs/log/p5.6.md), [plan](docs/log/p5.6-plan.md) |
| P5.8 iPad parallel Fli pacing | Done; [PR #17](https://github.com/farhaniqbalta/CheapWings/pull/17) merged `69f6417` | [P5.8](docs/log/p5.8.md), [plan](docs/log/p5.8-plan.md) |
| P5.4 More providers on iPad | Moved to the bottom by owner (2026-11-14): iPad is Fli-only for now; runs just before the web migration | |
| P5.7 Web backend onto the Rust core | Not started (web keeps all four providers in Python until then) | |
| P6 Release acceptance | Not started | |
| P7 Discover (Explore Anywhere / Surprise Me) | **Proposed / Not started** — separate feature beside Search (user chooses); awaits owner approval to start | [P7 plan](docs/06_IMPLEMENTATION_CHECKPOINTS.md#p7--explore-anywhere-proposed--not-started), [spec](docs/01_PRODUCT_REQUIREMENTS_UX.md#proposed-feature-explore-anywhere-and-surprise-me-p7--proposed--not-started) |

## Provider decision ledger
| Provider | Decision | Key limits (details in provider-feasibility-evidence / research logs) |
|---|---|---|
| Skiplagged MCP | GO, personal use only (owner 2026-11-09) | Terms ban commercial/redistribution; revisit before any public launch. No exact reprice; no per-segment identity for connections; hidden-city tag unconfirmed. |
| swoop | GO, personal/low-volume (owner 2026-11-09) | Undocumented Google RPC, ToS risk accepted; no hidden-city signal; price often an estimate; key offers off `booking_options`. |
| OctoTrip | GO, opt-in personal use (owner 2026-11-10) | Indicative only, no exact reprice, cache disabled; fare/fees/risk/source-age unknown; 900s lifecycle; nearby airports filtered. |
| Fli | Owner-requested personal-use integration (2026-11-12) | Google Flights public page; indicative quotes/search links; basic-economy exclusion unsupported; same inventory as swoop. |

## Latest checkpoint
- P5.8 (branch `p5.8-ipad-parallel-pacing`): iPad Fli requests start every 0.25 s with up to 6 open (web start-to-start logic), replies released in date order so saving and Resume are unchanged; stops cancel open requests and leave later days pending. Provider-neutral runner + `SearchProvider` protocol ready for P5.4. New app icon (taxiway direction sign, light/dark/tinted).
- Owner device checks passed ("it's way faster"; offline and cancel fine).
- Gates: Rust 28, backend 252, Swift Core 12 + Kit 71, iOS Release build.
- Details and rulings: [P5.8](docs/log/p5.8.md). Open: iOS 26 continued processing; web `providers/fli.py` whole-page currency rule; P5.6 deferred minors.

## Next task
P5.4 — more providers on the iPad (Skiplagged / OctoTrip adapters on the P5.8 `SearchProvider` seam; retry-after outcome, provider per work item). Plan first; owner reviews and merges every checkpoint PR. Docs refreshed after P5.8 (README, docs/README, 02, 05, 06, 08 now describe the standalone iPad app and the Rust core).

## Deviation log (approved design changes)
| Date | Change | Reason | Owner decision? |
|---|---|---|---|
| 2026-11-09 | Canonical itinerary gets explicit incomplete summary + nullable offer metadata/FX evidence | Skiplagged connections lack segments; swoop needs timezone reference; never fabricate | No (within spec) |
| 2026-11-09 | Add P4.5 UI/UX refinement phase | Owner requested | Authorized |
| 2026-11-09 | Polling-hook repair in P4.5 | Same-search refresh unmounted cards | No (corrective) |
| 2026-11-10 | Itinerary supports observed airport-change transfers + carrier display metadata | NRT→HND transfer rolled back a date; undeclared gaps stay invalid | No (corrective) |
| 2026-11-10 | Observation expiry separate from job budget; expired metadata returned with HTTP 200 | Owner-approved retention exception | Approved |

Full pre-restructure text of every section above: [baseline-and-old-summary](docs/log/baseline-and-old-summary.md).
