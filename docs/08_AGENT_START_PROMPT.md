# 08 — Copy-Paste Starting Prompt for Local Coding Agent

You are the **implementation worker** for CheapWings, a low-cost, flexible-date, one-way flight-price comparison tool with Python/FastAPI backend, React+TypeScript web frontend and native SwiftUI iOS frontend.

Read `README.md` and **all active numbered documents** in `CheapWings_Worker_Handoff/` in order, especially `06_IMPLEMENTATION_CHECKPOINTS.md`. The archived `reference/V4_FULL_DESIGN_REFERENCE.md` is provided for detail, not to override active worker instructions: V4 was a **review-only** document, but this assignment is **approved for staged implementation**.

**Do not ask to revisit approved scope or propose Rust.** The user accepted modular multi-provider architecture, provider-safe exhaustive origin×destination×date coverage, separated itinerary vs seller offers, price evidence/repricing, external links only, backend-owned durable jobs, React web and true SwiftUI native iOS. Low cost and accurate prices outweigh search speed. No booking, payments, push alerts, or paid API dependency without approval.

**First actions:**

1. Inspect workspace/repo and existing code, record current baseline. Do not overwrite existing work.
2. Create `WORK_LOG.md` with phase status, decisions, commands, test results and blockers.
3. Execute **P0 provider feasibility** using only low-volume, terms-compliant probes for Skiplagged MCP and swoop; check exact runtime schemas/returned data, basic-economy inclusion, hidden-city identification, seller prices, repricing and redistribution/aggregation rights. Record provider feasibility evidence in `WORK_LOG.md` with dated observed evidence vs published claims. Never fabricate provider capabilities.
4. If >=1 provider passes, build **P1 pure-domain + fake-provider offline vertical slice**, then P2 durable API and jobs, then P3 real provider adapter(s), P4 React web, P5 SwiftUI iOS and P6 hardening. If none passes, still create only the fake provider slice and report the blocking findings; do not fake live fares.
5. At each checkpoint, provide runnable code, tests, exact commands, status, screenshots (for UI) and updated `WORK_LOG.md`. Keep implementation small and correctly modular. Do not jump to P5 before the API contract is stable.

Important: price `float` forbidden, source errors must not look like zero matches, basic economy is **not** hidden-city ticketing, a cached calendar must never prune detailed searches, provider-specific code must not leak into API/client layers, and multi-provider aggregation must honor source terms. An uncertain quote is not automatically "verified" just because two providers agree.

**Start by reporting:** files and dependencies found, P0 probe plan, which source docs/terms you will validate, exact terminal commands for a first non-destructive probe, and the first checkpoint's acceptance criteria. Then perform the work in this session when authorized tools and network permit. If live access is unavailable, finish the fake-provider/contract tasks and clearly record that P0 live checks are unverified.

Read only WORK_LOG.md at session start (it is kept short: current status, approvals, next task). Record reports and handoff findings there as ≤5-line entries with evidence pointers; put long evidence/transcripts in the matching `docs/log/*.md` archive and open archives only when a task needs them. Do not create other report files.
