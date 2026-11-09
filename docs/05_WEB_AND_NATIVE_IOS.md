# 05 — Web + Native iOS Client Implementation

## Shared contract, separate UI

The product has **one remote search engine**. Web and SwiftUI are thin clients against `/api/v1`. They never connect to MCP, Google Flights, scrape pages or recalculate fare ranking. The backend owns search results, currency/fee policy and provider pacing. The mobile app is native, not React Native, a Rust UI framework or a wrapped website.

### Shared state machine

`idle → submitting → queued → searching → verifying → complete / partial / failed / cancelled`

But separate **job status** from **phase**: `running + verifying` is valid, `partial` is terminal with some failed work. Each client can resume with an authorized job id and refresh status; closing/refreshing UI does not cancel the server search.

Client screens:

1. **Search:** airport chips/selectors, earliest/latest date, one-way/one adult/economy fixed, advanced filters (max stops, baggage, basic economy, currency). Show `N route-date pairs` before submit.
2. **Progress + early results:** persistent progress bar, unique covered combos, provider state summary, last status update, provisional cheapest results while scanning. “Search in progress” is visible.
3. **Results:** default “Best checked deal” sorted by backend; secondary “Lowest advertised”; offer grouping with seller options, baggage, fare family, risk and source freshness.
4. **Details:** complete flight leg sequence (local datetime and timezone), layover duration, self-transfer warning, offer alternatives, verified vs indicative explanation and link scope.
5. **Recovery/error:** retry known failures when supported; failed/all-sources-offline state; restart/resume job; cancel job.

### Visual direction

Use a minimal, slightly warm neutral aesthetic; dense but readable information, generous touch targets. Avoid decorative destinations, maps, chatbots, fake airplane animations and marketing clutter. Price is visually dominant but not detached from status and baggage restrictions.

```text
iPhone:
┌───────────────────────────────┐
│ CheapWings             ⚙     │
│ Search cheapest flights       │
│ From: MEL   To: CGK DPS SUB   │
│ Departure: 12–20 Dec          │
│ [Search]                      │
│ 27 route-day pairs            │
│ Searching 21/27 pairs         │
│ Skiplagged ✓  Swoop 18/27     │
│                               │
│ Best checked deal             │
│ Rp ... [Repriced exact]        │
│ MEL → DPS  •  16 Dec  • 1 stop│
│ Bag: unknown  |  12h 20m      │
│ [See 2 sellers]               │
│                               │
│ Cheaper but unverified        │
│ Rp ... [Indicative]            │
└───────────────────────────────┘
```

All values and provider statuses in mockups are **illustrative, not actual search results**.

## React web app

- Vite + TypeScript. Recommend TanStack Query for polling/cache/error handling **if complexity justified**; otherwise typed `fetch` + small hooks is enough. No Redux or state management framework without a real need.
- Components: `SearchForm`, `AirportMultiSelect`, `DateRangeFields`, `SearchProgress`, `ProviderCoverage`, `ResultSortBar`, `ItineraryCard`, `OfferList`, `PriceStatusBadge`, `FareRiskNotice`, `JobErrorPanel`.
- React hooks: `useCreateSearch`, `useSearchJob`, `useSearchResults`, `useCancelSearch` over a single typed API module. No provider-specific hooks.
- Poll `/searches/{id}` and paginated results while active; cap polling, back off for long-running jobs; stop when terminal/unmounted. Avoid duplicate search creation on rerender and stale-result overwrites after new search.
- Keep job id in route or session state for recovery. Never store upstream tokens/selectors in local storage. For secure remote API, use approved user token/session storage.
- Empty/error states must distinguish `0 eligible fares` from `0 successful provider calls`. Show fetched-at/repriced-at timestamps in user locale and disclose that fares may change.
- Desktop: compact list/table with expandable rows; mobile web: card layout. Test responsive widths ~375 px, 768 px and 1440 px.
- Accessibility: semantic labels, input feedback, tab order, keyboard focus, button `aria` labels, loading announcements without noisy repeats, contrast, reduced motion.

## Native iOS SwiftUI app

**Create a real Xcode project** targeting a supported iOS version chosen at implementation time (document minimum deployment target and rationale). Use SwiftUI with:

- `SearchView`: airports, date range, stops, baggage, currency.
- `SearchViewModel` (`@Observable` or `ObservableObject` depending on deployment target): owns form validation and submission, no provider knowledge.
- `SearchJobView`: current backend job state and coverage, cancellation, retry when permitted.
- `ResultsView`: sorted itinerary group list and status labels; `ItineraryDetailView` for full segments and alternative sellers.
- `APIClient`: `URLSession` async/await over typed `Codable` structs. `SearchRepository` defines boundary for preview and test fakes.
- Secure auth tokens in Keychain when external deployment is supported; local-only credentials can be omitted only while local networking is trusted and private.

**App lifecycle:** iOS cannot promise uninterrupted arbitrary background polling. Server owns the search job, and app fetches progress/results on activation. Do not add iOS background modes or notifications without product requirement and platform justification. If app is offline, show last known results with `last_synced_at` and clear stale label; resume retrieval when online.

**iPad UI:** adaptive `NavigationSplitView` or roomy master-detail layout. Support Dynamic Type, accessibility reading order, 44 pt tap targets, light/dark mode system settings and localization-ready price/date formatting. Do not calculate custom currency conversions in the client.

## Shared API error translation

| API condition | User-facing behavior |
|---|---|
| `422` bad airport/date | Inline field correction, no job created |
| `429` job creation limit | Explain too many searches; retry later (no fabricated delay) |
| `5xx` backend error | Retry button, keep already saved job when available |
| Provider 429/timeout within a job | Show per-provider partial coverage; don't blank entire results |
| Job cancelled | Preserve completed results but label incomplete |
| Source link missing | Disable “Open offer,” explain seller link unavailable |
| Unknown bag / hidden-city risk | Avoid best-checked ranking; show explicit risk info |

## Frontend acceptance

- A fake-provider run renders identical priced offer groups and confidence labels in web/iOS.
- On app/browser refresh, a running job can be resumed, subject to authorization.
- Both clients display progress accurately when provider results arrive out of order.
- `repriced_exact` never appears when `is_estimate=true` or seller/brand mismatch was unresolved.
- No client hides provider failures or incorrectly asserts that checked-bag restrictions are absent.
- Critical UX tests cover full range, empty success, all failure, partial success, cancellation, changed price and unavailable link.

## Platform priority

**Implement web first, iOS second** after REST/OpenAPI contract passes tests. This is an execution order, not a reduction of native-iOS scope. Maintain Swift models and feature list from the same contract, rather than reimplementing domain rules on iOS.
