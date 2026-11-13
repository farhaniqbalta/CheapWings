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
- Country-wide auto-expand airport codes or route suggestions in **Search** (user selects concrete IATA airports; curated Major airports since P4.10/P5.5). Route discovery is the separate proposed **Discover** feature below and does not change Search.
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

## Proposed feature: Explore Anywhere and Surprise Me (P7 — Proposed / Not started)

> **Status: proposal for owner approval, not an approved requirement.** Nothing here is
> implemented. Milestone: [06 → P7](06_IMPLEMENTATION_CHECKPOINTS.md#p7--explore-anywhere-proposed--not-started).
> Architecture: [02 → destination discovery layer](02_SYSTEM_ARCHITECTURE.md#proposed-destination-discovery-layer-p7--not-approved).
> Provider candidates: [03 → discovery candidates](03_PROVIDERS_AGGREGATION_PRICING.md#destination-discovery-candidates-p7-research--unverified).

### What the user does

**Explore Anywhere:** pick an origin (airport, or a city/country's Major airports as in the
iPad picker), a flexible departure date range, and optionally a maximum flight budget (in the
display currency) and destination limits (region/country include or exclude lists, max
stops). CheapWings finds destinations that look affordable, checks real fares for a bounded
shortlist with the existing detailed search, and shows destinations ranked by the best fare
evidence found.

**Surprise Me:** the same request, then CheapWings picks one (or a few) destinations at random
from the Explore Anywhere results that meet the budget and limits. It is a presentation mode
over the same results — no separate search engine, scheduler or provider path.

### Price evidence shown per destination (never merged)

| Level | Meaning | Ranked as |
|---|---|---|
| Discovered destination | A source suggests the route exists / is popular | Not a price |
| Discovery price | Historical, cached or "from" price from a discovery source, with its age | `indicative` only, labelled "from … (source, age)" |
| Checked offer | Fresh detailed search result for a real route/date | `recent_search` (same rules as today) |
| Verified fare | Exact reprice, only where a provider supports it | `repriced_exact` |

A destination's headline price is the best **checked** offer when one exists; a discovery
price alone is shown separately and never ranks above checked offers or wears a checked badge.

### MVP (if approved)

- One origin side (one or more airports), date range within the existing 120 route/date cap.
- Discovery from **one** feasible, permitted source; candidates normalized to catalog airports,
  deduplicated, filtered by budget/limits, then a bounded shortlist (e.g. top N destinations ×
  dates within the cap) sent to the existing detailed search (Fli first, as today).
- Progressive results: discovered list appears first (clearly "not checked yet"), checked fares
  fill in as the normal search progresses; coverage line "checked N of M candidate
  destinations".
- Surprise Me as a button on the finished (or partial) Explore results.
- A top-level choice between **Search** and **Discover** on web and iPad; Search's form and
  results stay as they are.
- Web and iPad both, sharing the Rust selection logic; same result order for the same inputs.

### Later enhancements (not MVP)

Multiple discovery sources merged; region presets and maps; trip-length / return-date
exploration (roundtrips are out of scope today); "weekend" date presets; saved explore
searches; Surprise Me constraints (e.g. "somewhere new", visa-free lists — needs a data source).

### Non-goals

Brute-force search of hundreds of airports × dates; treating discovery prices as bookable;
price alerts or historical-price analytics; booking; a second search engine or scheduler for
Explore or Surprise Me; moving networking or UI into Rust.

### Relationship to Search (owner decision, 2026-11-14)

**Search** (today's feature) and **Discover** (Explore Anywhere + Surprise Me) are two separate
features. The user chooses Search or Discover in the app (web and iPad). Search keeps all of its
rules unchanged — exhaustive route/date coverage, non-negotiable #4 in
[docs/README.md](README.md) ("calendar prices only prioritize, never prune"), concrete airport
selection. Those rules govern Search only; Discover has its own rules in this section (bounded
shortlist, "checked N of M candidates", never "cheapest anywhere"). So the two do not conflict.

Discover reuses Search's engine (detailed search, scheduler, pacing, cache, persistence, Rust
core) but is not a mode of the Search form.

### Decisions and deferred questions (owner, 2026-11-14)

| # | Question | Status |
|---|---|---|
| 1 | Which discovery source is permitted alongside other providers | Open — decided in P7.1 feasibility |
| 2 | Budget semantics (fare type, currency, FX for "from" prices) | **Follows the future discovery API contract** (P7.2) |
| 3 | Shortlist size / destinations vs the 120 cap and pacing | **Depends on the chosen discovery provider** (P7.1/P7.3) |
| 4 | How the user reaches it | **User chooses Search or Discover**; platform delivery per provider reachability |
| 5 | Surprise Me randomness (seeded vs fresh) | Deferred — explore later |
| 6 | Region definitions (catalog countries vs curated regions) | Deferred — explore later |

Owner input: the candidate providers expose destination/price APIs for this, so the shared
Rust engine can still serve Discover on both web and iPad (to be confirmed per source in P7.1;
the candidates in 03 remain unverified until probed).

### Risks

Discovery data stale or geographically biased (popular routes only); source terms forbidding
aggregation (Travelpayouts Search API rules already flag this); undocumented endpoints
breaking (Google Explore); extra load on Fli if shortlists are too large; users reading
"from" prices as fares.
