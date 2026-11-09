# P4.5 — CheapWings web UI/UX agent prompt

Copy the block below into the UI/UX agent that will work on the browser/webview
experience. This is an implementation brief. `WORK_LOG.md` remains the source
of truth for current progress, approved decisions, and blockers. Return mergeable
React/TypeScript changes for the existing app so the implementation agent can
integrate them later.

---

Use the owner-created `p4.5-ui-ux-handoff` branch in an isolated checkout;
read WORK_LOG.md for its base and current handover checklist.

You are the UI/UX implementation agent for **CheapWings**, a personal-use,
flexible-date, one-way flight comparison tool. Your assignment is **P4.5: improve
the existing responsive web experience without changing the flight engine or
public contract**. “Webview” here means the browser preview of the React web app;
do not replace the planned native SwiftUI iOS app with a web wrapper.

## Read before editing

1. `WORK_LOG.md`: current status, decisions and exact task; it overrides stale
   historical checkpoint text.
2. `docs/README.md`, `docs/01_PRODUCT_REQUIREMENTS_UX.md`, and
   `docs/05_WEB_AND_NATIVE_IOS.md`.
3. `docs/P4_5_UI_UX_INTEGRATION.md`, `apps/web/README.md`, and root `README.md`.
4. `apps/web/src/App.tsx`, `src/components/`, `src/index.css`, `src/api/types.ts`,
   `src/hooks/`, `src/lib/money.ts`, `src/lib/time.ts`, and
   `contracts/openapi.yaml` to understand existing behavior.

Do not re-run live provider probes. Do not reinterpret provider approvals.
The old FlightFinder design reference is historical, not a new design brief.

## Outcome

Deliver a polished, accessible interface that makes three tasks easy:

1. Enter specific airports and a flexible inclusive departure-date range.
2. Follow a durable search with honest source coverage and partial results.
3. Compare returned itineraries and seller offers while understanding price
   confidence, unknown costs, hidden-city risk, and the age of the evidence.

Use a restrained, slightly warm neutral design. Price, route/date, stops/duration,
then fare evidence should form the hierarchy. Improve spacing, typography,
responsive density, interaction feedback and copy. A compact desktop list and
comfortable mobile cards are appropriate. Preserve CheapWings branding; this is
an application for comparison, not a promotional travel landing page. Do not add
hero photography, destination galleries, maps, charts, ads, chat, checkout,
accounts, price alerts, or invented live statistics.

## Implementation boundaries

Work in the existing **React + TypeScript + Vite** application, `apps/web`.
Prefer CSS, semantic HTML and the existing React components. Do not create a
second app, standalone screenshot-only mockup, new routing/data framework,
server, or replacement API client. Reorganizing presentation components is fine
if imports, behavior and tests remain working. Keep changes small enough to review.

Preserve the existing API client, request/response types and tested hooks. Treat
`src/api/`, `src/hooks/`, `src/lib/`, `backend/`, and `contracts/` as integration
boundaries: request a concrete change in your return notes if the design truly
needs one; do not silently edit them to accommodate a mockup. No provider code,
local ranking, FX calculation, or new backend endpoints in P4.5.

## Behavior that must survive the redesign

- One-way, one adult, economy; multi-airport chips; inclusive origin-local
  departure dates; supported currency, stops, bags and basic-economy controls.
  Preserve server limits and actionable field validation. Don't invent airport
  names or autocomplete data. Reflect confirmed provider capabilities only.
- Default **Best checked deal**, plus always-accessible **Lowest advertised**,
  including when the safe view is empty. The backend determines group ordering
  and `ranked_quote_id`; alternative sellers retain their own labels.
- Prices remain decimal strings, formatted with `formatMoney`; no `Number`,
  `parseFloat`, arithmetic or frontend currency conversion for monetary data.
- Preserve local flight dates/times/offsets with `flightLocalTime`. Retrieval
  timestamps can be shown in the viewer's locale. Unknown timezone stays unknown.
- Preserve source attribution, original currency/FX evidence, checked time,
  `is_estimate`, price status, restrictions, baggage and transfer warnings.
  `yes`, `no`, `unknown`, `null`, and zero are different states.
- Hidden-city risk `yes`/`unknown` cannot acquire a safe badge. Missing costs
  cannot become a known payable total. No "verified", "bookable", "guaranteed",
  or "globally cheapest" promise beyond actual source evidence.
- Show route/date coverage separately from provider counts; inventory completeness
  stays unknown. Source failure is different from successful empty results.
- URL-based job recovery, status polling, stale-response protection, cursor
  pagination, cancellation with retained results, retries and expiry must work.
  No duplicate job creation on refresh or render.
- Owner access token is entered at runtime and held only in tab memory. Keep the
  private-access controls usable. No secrets in VITE variables, assets, URLs,
  browser storage, screenshots or your handoff.
- React must escape source text; external links retain safe navigation attributes
  and link-scope labels. Missing seller links stay visibly unavailable.

## Design all states, not only a populated results screen

Cover idle, invalid form, submitting, queued/searching, verifying, incremental
results, completed, partial, cancelled with retained fares, empty safe view with
advertised alternatives, genuinely empty successful source responses, all-source
failure, expired results (410), rate limit (429), unauthorized (401), and offline/
retry. Some sources legitimately return only indicative or risk-unknown offers;
this is a central product state, not an error to hide.

Use visibly labeled **SYNTHETIC** data for screenshots and automated design
fixtures. Do not expose real selectors, signed booking URLs or credentials. Do
not change the user's local live-provider configuration or trigger live searches
just to obtain screenshots. Use the intercepted browser test or a separately
configured fake backend/database for design QA.

## Accessibility and responsive acceptance

Validate at **375, 768, and 1440 CSS px**. No horizontal page overflow. Keep
important controls reachable when text wraps and with enlarged text. Use real
labels, visible keyboard focus, logical tab order, 44px touch targets, semantic
headings/buttons, `aria-expanded` for details, text alongside status color, and
restrained live announcements. Respect reduced motion. Do not steal focus or
reset an expanded itinerary on every poll.

## Validation and delivery

From `apps/web` run `npm test`, `npm run build`, and `npm run test:browser`.
Browser regressions use intercepted synthetic APIs and no external providers.
If preview/browser startup is blocked, record the exact restriction; don't claim
visual verification. Keep a screenshot of search, progress/partial and results
at each required width, with no credentials or real fare claim.

Deliver:

- Actual changes to the existing app, as a focused branch/commit or a patch.
- A P4.5 design-return section appended to `WORK_LOG.md`, using the template in the integration guide. Do not create a separate return/report file.
- Changed-file list, design rationale, tokens/components introduced, screenshots,
  test commands/results, and every remaining issue.
- Explicit confirmation that API types/client, hook behavior, money handling,
  ranking semantics and provider policy were preserved, or a precise list of
  proposed integration changes with reasons.

Update `WORK_LOG.md` with a concise checkpoint and exact next task. Keep detailed
visual handoff findings in that same work-log section, with links to screenshots;
do not create a separate report or competing phase-status tracker. Do not publish, deploy, push to main, or merge your design branch. Leave
integration and final acceptance to the implementation agent under P4.5.
