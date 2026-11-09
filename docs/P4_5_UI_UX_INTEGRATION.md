# P4.5 — Web UI/UX integration contract

This guide defines how a design agent's output will enter the existing CheapWings
web application. Current phase status and decisions belong in `WORK_LOG.md`.
The design assignment is the [copy-ready prompt](P4_5_UI_UX_AGENT_PROMPT.md).
P4.5 refines the web client; it does not replace native iOS P5.

## Work area and merge boundaries

Start from the latest committed web implementation after reading WORK_LOG.md.
Record the base commit SHA in the return file. Prefer an isolated design branch
or checkout; never overwrite another agent's uncommitted work.

| Area | Design-agent scope | Integration requirement |
|---|---|---|
| `apps/web/src/index.css` | Colors, typography, spacing, layout, states, focus | Keep responsive behavior and reduced-motion support |
| `apps/web/src/components/` | Presentation structure, accessible interaction and copy | Preserve props/contracts or provide explicit prop migration map |
| `apps/web/src/App.tsx` | Screen composition and local visual controls | Keep job URL recovery, token application, sort, pagination, retry and cancellation wiring |
| `apps/web/src/assets/`, `public/` | Necessary small local assets only | Document provenance; no trackers, remote secrets or decorative asset bulk |
| `apps/web/src/api/`, `hooks/`, `lib/` | Read to integrate; propose changes separately | Preserve tested runtime auth, polling, monetary strings, local times and API semantics |
| `apps/web/tests/` | Add presentation/accessibility regressions if needed | Retain existing regression assertions; no live provider calls |
| `backend/`, `contracts/`, `.env*` | Outside design scope | Never change adapters, ranking, DTOs, deployment or the owner's configuration |
| `WORK_LOG.md` | Append checkpoint, refresh relevant current status | Sole source of truth for phase state; retain previous evidence |

Do not rename the package, re-scaffold Vite, replace the app with static HTML,
install a design framework by default, or add mock prices to production components.
If a library is essential, explain why existing CSS/React is insufficient, list
license/bundle impact, and provide the lockfile change for implementation review.
No skill, hosting, browser-webview wrapper or deployment change is part of P4.5.

## Existing components to retain or map explicitly

| Component | Behavior to preserve |
|---|---|
| `AirportMultiSelect`, `SearchForm` | Real field labels, chip editing, inclusive date range, validation and query count |
| `SearchProgress` | Job status and phase, unique route/date vs provider coverage, cancel and partial warnings |
| `JobErrorPanel` | Errors distinct from empty success; actionable retry/auth/expiry states |
| `ResultSortBar` | Safe vs advertised views accessible even for zero safe offers |
| `ItineraryCard` | Origin-local dates/offsets, stops/duration, incomplete identity, expandable full segments |
| `OfferList` | Distinct seller offers, backend-ranked quote, original/converted amount evidence and attribution |
| `PriceStatusBadge`, `FareRiskNotice` | Actual estimate/price/risk status; no optimistic substitution of unknown fields |

`api/types.ts` follows the committed OpenAPI contract. It is handwritten because
this scaffold's TypeScript version did not fit the generator's peer requirements.
Design work must not generate a different contract from illustrative docs examples.

## Data and interaction acceptance cases

| Case | Acceptance check |
|---|---|
| Safe results empty, advertised offers exist | Sort remains reachable; unknown-risk/indicative offers have clear caveats |
| Source succeeded empty | Copy says no matching fares returned by searched sources; never no flights exist |
| Provider partially fails | Successful results stay visible; source failures and coverage remain explicit |
| All sources fail | Failure state, no empty-success presentation |
| More than one results page | Load more appends the same snapshot; switching jobs/sorts fences old responses |
| Refresh/reconnect | Existing job is recovered from URL; no second POST; runtime token re-entry remains possible |
| Cancel | No fresh work scheduled; displayed completed fares retained with incomplete/cancelled label |
| 401 / 410 / 429 | Runtime auth / start fresh / quota retry guidance; backend string errors render cleanly |
| Incomplete identity or unknown timezone | No fabricated segments, carrier, timezone, transfer or exact badge |
| Original vs converted price | String precision retained; FX evidence and source amount remain inspectable |
| Live source provenance | Attribution and source timestamps visible; signed selectors/handles absent |

The browser suite at `apps/web/tests/browser.mjs` already exercises four critical
flows with synthetic intercepted responses. Add targeted checks for your layout
changes. Do not remove assertions merely to make a redesigned screen pass.

## Designer return template

Create `docs/design/P4_5_RETURN.md` with these fields when delivering design work:

```markdown
# P4.5 design return

Base commit:
Design branch / commit / patch:
Changed files:

## Design rationale
Primary tasks improved; hierarchy, responsive choices and accessibility.

## Component/prop map
Old component → new file/name/props, or confirm unchanged.

## Tokens and assets
CSS custom properties; typography; local asset provenance; dependency changes.

## Interaction and evidence preservation
Confirm job recovery/polling, cancellation, sorting, pagination, auth, money strings,
source-local dates, coverage, risk/unknown metadata, attribution and links.
List every intentional behavior change separately.

## Visual evidence
375 / 768 / 1440 screenshots of form, progress/partial and results.
All sample fares visibly synthetic; no credentials, selectors or signed URLs.

## Validation
Exact commands, pass/fail results and browser/keyboard checks actually run.
Record environment restrictions and any unverified cases.

## Integration requests and remaining issues
Backend/API/hook changes proposed (do not silently implement), tradeoffs and TODOs.

## Next smallest task
Concrete instruction for the implementation agent.
```

## Implementation-agent integration sequence

1. Re-read WORK_LOG.md and compare the return's base SHA to current main. Inspect
   the changed-file list before applying the branch or patch; preserve newer
   functional fixes and local provider configuration.
2. Apply focused presentation changes, resolve imports/props explicitly, and reject
   any production mock-data fallback or local reimplementation of ranking/FX.
3. Run backend tests from root, then `npm test` and `npm run build` in `apps/web`.
   Run `npm run test:browser` with Chromium available. Test real API integration
   with fake providers in a separate DB; do not use live calls for design QA.
4. Check 375/768/1440, keyboard focus, enlarged text, status copy, empty-safe versus
   advertised state, pagination, refresh and cancellation. Verify the artifact
   contains no owner token or opaque provider handle. Keep screenshots if feasible.
5. Record actual checks, deviations and unresolved issues in WORK_LOG.md. Commit
   the reviewed P4.5 change; merge/push only with the owner's existing authorization
   for that integration. Then resume P5 according to full-Xcode availability.

A successful screenshot alone does not close P4.5. The integrated existing React
app must build, retain the durable search behavior, and pass the stated checks.
