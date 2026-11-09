# 01 — Product Requirements, Rules, and UX Acceptance

## Product position

A **flexible one-way cheapest-flight finder**, not a booking site and not an airfare-prediction tool. A user is willing to wait for broad date/airport coverage and rechecks. Communicate “cheapest eligible fare **found by the enabled providers under these conditions**,” never “world’s cheapest ticket.”

### In scope — MVP P0

- One-way, 1 adult, economy. Keep trip type and passenger model extensible but do not implement roundtrip or multi-passenger.
- Inclusive origin-local departure dates. One or more origin and destination IATA codes; validate code shape and airport-code reference where available. Reject same-origin-and-destination pair, duplicates, bad dates, expired windows or excessive query sizes with actionable errors.
- Optional max stops, checked-bag requirement, include-basic-economy setting, currency (IDR initial default), and point-of-sale country if supported consistently.
- Every valid origin × destination × date is attempted by enabled detailed-search providers unless the specific provider is explicitly unsupported, disabled, forbidden under terms, or job cancelled. Show how many scheduled, attempted, successful, empty, failed, unsupported.
- Deduplicate identical itineraries conservatively while retaining **distinct provider/seller/fare offers**.
- Compare fare amounts only when equivalent on currency, passengers, cabin, taxes/mandatory fees, requested bags, and known restrictions. Do not present unknown required extras as a definitively cheaper total.
- Current or recent detailed offers, exact-offer repricing when available, meaningful timestamps, confidence status, external link when valid.
- Server-managed long search jobs, web/iOS polling, cancellation, restart recovery and partial results.
- Normal hidden-city ticket exclusion by default. If cannot confirm whether a candidate is hidden-city, mark `risk_unknown`; exclude from default “safe cheapest” tier. Do not conflate basic economy with hidden city.
- Logging, observable errors, data source metadata and source terms check.

### Not in MVP

- Direct booking, payment, ticketing, accounts/PII, multi-city, roundtrips, hotel/car extras.
- Background price alerts, notifications, price predictions, historical price analytics.
- Country-wide auto-expand airport codes or route suggestions (user selects concrete IATA airports).
- Upstream anti-bot circumvention, proxy rotation to evade controls, captcha bypass, unauthorized data extraction.
- Push notifications, offline fare searches, local iPhone provider clients, local LLM.

## Search and ranking rules

1. Expand unique valid pairs for each local departure calendar date. Eg. 1 origin × 3 destinations × 9 dates = 27 combos.
2. Calendar results are optional **scheduling hints**, not proof the cheapest dates have been exhaustively identified. Detailed provider searches must still cover eligible combinations.
3. If a provider has a real bulk-date detailed search, use it only if its actual observed response covers the requested matrix to the same standard.
4. Each successful provider search may return only top N results. Track coverage of **queries** separately from completeness of **flight inventory**, which usually remains unknown.
5. Normalize original money; preserve quoted and comparison FX evidence. Same trip ≠ same offer.
6. Reject unsafe (`hidden_city=true`) offers from default normal-ticket ranking; route risk/unknown in separate clearly identified section.
7. Include basic-economy fares if available and configured, but label bag/carry-on/fare restrictions. Unknown baggage cost must remain unknown.
8. Price states and ordering (most conservative): `repriced_exact` (same fare product/selection, non-estimate), `recent_search` (detailed response), `indicative` (calendar/old/estimate), `changed_or_unavailable` (not current). A “repriced” result is **not a checkout guarantee**.
9. Default “Best checked deal” prioritizes comparable *recently repriced* offers, with recent detailed offers after; show a separate `Lowest advertised` sort including uncertain prices with warnings. Do not bury cheaper unverified fares.
10. Do not claim price accuracy based on coincidentally equal prices from two aggregators; true repricing should check the same itinerary and comparable fare, preferably seller.
11. External links may open airline/OTA search/offer page, but label if generic/not tied to exact itinerary. Never fake a direct purchase link.
12. Provider errors or incomplete coverage must remain visible in search header and final report.

## Form UX

**Fields:** From airport chips; To airport chips; earliest and latest departure dates (inclusive); one-way indicator; 1 adult; economy; currency IDR; `Max stops` (Any/0/1/2); checked bag (No / Required); `Include basic economy` (on by default); optional advanced source settings if operationally useful.

- Validate on submit, show count of route-date combinations and honest note that a search may take time. Do **not** show fake time estimates.
- If search exceeds configured caps, display concrete scope problem (e.g., “too many airport × date combinations”) and how to narrow it.
- Allow restart/retry failed pairs when backend permits, not duplicate completed work blindly.

## Results screen and states

```text
CheapWings                                              [Settings]
Find the lowest priced eligible one-way flights across flexible dates

From [MEL]   To [CGK] [DPS] [SUB]   Departure [12 Dec]–[20 Dec]
1 adult · Economy · IDR · Max stops: Any · Checked bag: Not required
[Find cheapest flights]

Coverage: 27 / 27 route-date pairs (at least one source responded)
Provider coverage: Skiplagged 27/27 · swoop 25/27 + 2 timed out
Inventory completeness: Unknown · Reprice: 8/10 checked · [Retry errors]

[Best checked deal] [Lowest advertised] [Fewest stops] [Shortest trip]

Rp ...  MEL → DPS | 16 Dec | 1 stop | Repriced exact
Seller / provider · fare class · baggage · 12h 20m · Checked 14:03 [Open]

Rp ...  MEL → CGK | 18 Dec | nonstop | Recent search
... [Offer details: alternative sellers for same flights]

Cheapest unverified: Rp ... [Indicative — seller price may differ]
```

> Every listed price above is a placeholder, not live data.

### States that must be implemented

| State | Display |
|---|---|
| Idle | Empty form; concise product limitation |
| Validating | Invalid fields and query cost preview |
| Queued/running | Progress by combination + provider; results can arrive incrementally |
| Verifying | Results retained; targeted fares show pricing-check indicator |
| Partial/incomplete | Explain which combinations or sources failed; offer retry |
| Complete | Cheapest eligible found among covered sources, timestamps, caveats |
| Empty after success | “No matching fares returned in searched sources” — not “no flights exist” |
| All providers failed | Error summary, never empty-success |
| Cancelled | Preserve already discovered offers; explicit incomplete status |
| Price changed | Replace ranking with rechecked amount, optionally show original quote |
| Source disallowed/disabled | Inform user which providers were not included |

## Visual direction

- Minimal, utilitarian, clean neutrals. Card-first on iPhone; compact table/list on desktop. Stable layout while results stream/poll.
- Hierarchy: price > route and date > stops/duration > fare/verification/seller; filters do not overshadow the cheapest result.
- Status colors only for semantic differences. Text labels always accompany colors/icons.
- iPad: adaptive two-column form/results or comfortable wide list, not an enlarged iPhone mockup.
- Accessibility: VoiceOver labels, 44pt touch targets, Dynamic Type, keyboard navigation on web, local date/time shown with timezone context.
- No ad cards, map UI, charts, AI prompts or irrelevant decorative visuals in MVP.

## UX acceptance tests

- A 9-day range with 3 destinations produces 27 valid combinations and the UI reflects the difference between route-date and per-provider coverage.
- An early low-priced **indicative** offer never inherits a repriced badge from another offer on the same flight.
- A seller price changes during repricing: results update, old amount is not ranked as current.
- Baggage-required with unknown baggage cost: candidate is labeled price-incomplete, not best confirmed deal.
- User closes iPhone app and later opens it: search continues on hosted server and job state can be recovered.
- Provider fails on 2 of 27 combos: app says `partial`, never `100% complete across providers`.
- All sample fares must be clearly fictitious in demos, screenshots and tests.
