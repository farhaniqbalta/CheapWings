# 03 — Provider Feasibility, Multi-Provider Aggregation, and Fare Accuracy

> **First engineering gate (P0).** Implement provider probes and record actual observations **before** integrating live providers into the app. Documentation can describe advertised capabilities, not prove them.

## Initial provider candidates

| Source | Intended role | Starting evidence | Critical risks |
|---|---|---|---|
| **Skiplagged remote MCP** | Calendar discovery + detailed search | Official docs: https://skiplagged.github.io/mcp/ ; endpoint `https://mcp.skiplagged.com/mcp` | Indicative prices, hidden-city offers, response schema/quotas/terms to validate |
| **swoop (Python)** | Google Flights detailed searches + selected-trip pricing | Repo: https://github.com/saraswatayu/swoop | Undocumented Google RPCs, breaking changes, blocking calls, estimates, acceptable use |
| **omkarcloud/google-flights-scraper** | Optional calendar experiment, not primary | https://github.com/omkarcloud/google-flights-scraper | Chrome dependency, fragility, low independent validation |
| **SerpApi calendar** | Optional hosted fallback | https://serpapi.com/google-flights-calendar-api | API key, cost, cached price, terms and quota |
| **Travelpayouts Search API** | **Not an aggregation adapter by default** | https://support.travelpayouts.com/hc/en-us/articles/34788165535250-Search-API-usage-rules | Published rules prohibit combining Search API with other flight metasearch APIs; don't enable without documented permission |

Never assume a provider is free forever, has permission for multi-source redisplay, or supports the same fare product as another provider. Keep availability and legal status configurable. The exact provider inventory may change; **do not invent replacements**.

## P0 provider probe checklist (mandatory)

Run only low-volume requests compliant with each provider's terms, ideally for a real future international one-way route/date with manual browser verification:

- [ ] Inspect official documentation, usage terms, license, authentication, per-client budget, permitted storage/caching/aggregation/redisplay.
- [ ] Pin SDK/package version. Log repository version/commit and observation date.
- [ ] For MCP: invoke `tools/list` at runtime; record actual tool names, schemas, field types, date-window constraints, supported currency, real response shape. Do not rely on inferred schema.
- [ ] For `swoop`: demonstrate `search()` and (if allowed) `price_selector()` or equivalent exact-fare method; verify `SearchResult.is_complete`, `PriceResult.is_estimate`, basic-economy toggle, booking-seller result availability.
- [ ] Validate origin/destination codes and inclusive local dates; distinguish calendar from detailed offer response.
- [ ] Capture **sanitized** result and response/UTC timestamp, price/currency/fee details, segments, stop count, fare brand, baggage, links, confidence/estimated flags.
- [ ] Attempt a low-cost comparison with the supplier/airline website at the same time if available; note exact seller/flight/fare match, checkout vs search estimate, point-of-sale currency differences.
- [ ] Determine how to **identify or exclude hidden-city tickets**; if impossible, default those candidates to risk-unknown outside safe ranking and report diminished coverage.
- [ ] Test “no flights” vs errors vs throttling vs incomplete returned list, basic-economy-included and excluded, and cancellation/timeout behavior.
- [ ] Check if one provider's own multi-destination API returns the same data as separate route-date requests; don't infer equivalence.
- [ ] Record GO / CONDITIONAL GO / NO-GO **per provider**, with minimal evidence and integration implications.

**Proof of Concept deliverable:** [the provider feasibility evidence log](log/provider-feasibility-evidence.md) with a table of claims vs observed data, permission notes, dated references, redacted fixtures, exact probe command, route/date, failure logs, manual price comparison and verdict.

## Provider adapter contract

Use a typed internal abstraction. Components outside adapters deal in canonical values only:

```python
class SearchProvider(Protocol):
    provider_id: str
    capabilities: ProviderCapabilities
    async def search(self, query: SingleDateRouteQuery) -> ProviderSearchResult: ...

class CalendarProvider(Protocol):
    async def calendar(self, query: CalendarQuery) -> ProviderCalendarResult: ...

class RepriceProvider(Protocol):
    async def reprice(self, handle: ProviderQuoteHandle) -> ProviderRepriceResult: ...
```

`ProviderSearchResult` includes source completeness (`true/false/unknown`), source quote timestamp if exposed, `retrieved_at`, sanitized evidence pointer, raw metadata needed for future debugging, results and explicit error taxonomy. No adapter mutates the shared canonical domain model after returning it.

**swoop-specific design:** It is a Python library and some calls are synchronous; run from a bounded executor. Explicitly pass `include_basic_economy=True` when policy requires; the published default is false. Expose `is_complete`/`is_estimate` and opaque selector only to its own repricing adapter. `check_price()` by flight number alone can select a different fare than the original offer—prefer selector-based exact itinerary when supported and inspect seller/brand. Source: https://github.com/saraswatayu/swoop.

**Skiplagged-specific design:** Its displayed non-USD amounts are approximate USD conversions; original USD and source FX metadata must be preserved. Returned quotes may be indicative. Default price ranking should not silently include hidden-city options. Do not claim its MCP includes a direct **exact seller repricing** operation unless P0 proves it. Source: https://skiplagged.github.io/mcp/.

## Canonical model and identity

An **itinerary** is an ordered sequence of individual flight segments and connection/ticketing relationships, not `MEL-DPS-2026-12-16` alone. Key fields per segment: actual origin/destination, local departure and arrival with TZ/UTC instants, airline marketing + operating carrier, flight number, and sequence. Two routings with different segments are **different itineraries**.

A **quote/offer** is a price from a given provider and seller for a specific itinerary and fare product, with fare family/cabin, bag allowance, fees, currency, point-of-sale, evidence and timestamp. One itinerary can have multiple sellers and multiple fare classes; **do not collapse them**.

### Matching algorithm (conservative)

1. Parse complete segments with UTC instants and flight numbers. Normalize flight numbers/carrier codes carefully but **never fabricate** missing timezones or identifiers.
2. If all identity-critical fields are present, build a stable canonical fingerprint over the ordered segments. Include service date and airports. Check codeshares/operating-vs-marketing carrier before treating differences as identical.
3. If two providers have identical segment sequences and schedules but different seller/fare tiers, group the itinerary and preserve separate offers.
4. If required segment identity is missing/ambiguous, do **not** force-match based on route, price or approximate departure time. Keep as separate “unmatched itinerary” with a warning.
5. A provider sending an updated quote for the same seller/product creates a quote revision/updated offer with history, not a new fake flight.
6. Flight cancellation, schedule change or different connection/transfer should produce a new identity/explicit mismatch, not automatically update unrelated quotes.
7. Duplicate source responses for the same exact provider quote handle must be idempotent; do not inflate result counts.

### Example (synthetic)

| Itinerary | Provider | Seller | Product | Price | Should merge? |
|---|---|---|---|---|---|
| Airline XY123 + XY456 | Skiplagged | OTA A | Saver / cabin bag | IDR 2.85m | Same itinerary grouping only |
| Airline XY123 + XY456 | swoop | Airline XY | Basic / personal item | IDR 2.72m | Same itinerary grouping, **distinct fare** |
| Airline XY123 + XY789 | swoop | OTA B | Basic | IDR 2.60m | **Different itinerary** |

No example is a real quote.

## Comparable monetary totals

- `Money` = exact `Decimal` amount or integer minor units + ISO currency; preserve the raw source amount with precision and currency semantics. No floating point for money.
- Original fare and exchange rate must be kept with source, timestamp and rounding precision. A single FX snapshot is used for normalized comparison; original price remains visible.
- IDR minor exponent is zero by ISO convention; provider-supplied subunit/rounding conventions must be validated. Do not assume every currency has two minor units.
- `comparable_total` is only trusted when total fare and mandatory taxes/fees are known and selected required baggage is covered (or verified additional bag fee added). Otherwise `comparison_status=missing_required_costs` or similar.
- Do **not** add imaginary baggage, seat, card or transfer fees. Expose unknowns. If no bag required, basic economy can be ranked with restriction clearly shown.
- Point-of-sale and exchange rate choices must be recorded. When two sources differ materially in cabin, fare brand, POS country or estimated bag, surface non-equivalence; don't claim a “same fare” match.

### Ranking tiers

**Default view — Best checked deal:**
1. Eligible, comparable, current **exactly repriced** offers, sorted by normalized payable total.
2. Eligible, comparable **recent detailed search** offers, clearly marked lower confidence.
3. Indicative/estimated/price-incomplete offers in a separate “Possible lower prices — verify” section.

Expose `Lowest advertised` as an alternative view (the cheapest number including unknown-cost/indicative candidates) **with visible caveat**. Don't claim a given price is guaranteed available. Include `Shortest duration` and `Fewest stops` optionally.

Use a finite freshness policy from config, but **don't convert an old reprice into a fresh quote** by changing `retrieved_at`. Timestamp terminology:
- `retrieved_at`: when our adapter received result;
- `source_checked_at`: when provider says quote was computed (optional);
- `repriced_at`: when a matching exact itinerary/fare was successfully rechecked;
- `fx_as_of`: timestamp of conversion rate.

## Repricing workflow

1. Maintain a candidate shortlist: start with **10 cheapest eligible offers plus near-price competitors within 10%**, subject to configured cap; thresholds are initial hypotheses requiring P0 measurement.
2. Include representation from each enabled provider and relevant airport/date competitor; don't let one provider monopolize repricing budget.
3. Reprice using the **originating provider's** exact offer handle where supported. Check exact segments, passenger count, cabin, brand, seller, currency and POS. Mismatch = **new distinct offer or failed reprice**, not a successful validation of old price.
4. Record amount revisions and source time. If changed/inapplicable, update ranking, flag old result and move down shortlist.
5. If no exact-reprice endpoint, retain as `recent_search` or `indicative` with the weakest justified label. Cross-source agreement alone is not exact repricing.
6. If all verification fails, return lower-confidence fares with honest explanatory status. Do not block all useful results.
7. Offer link may be exact or generic; store `link_scope` and let UI label appropriately.

## Provider licensing and compliance

- `provider_registry` should include `enabled`, `permitted_to_aggregate`, `can_cache`, `attribution_required`, retention limits, `usage_policy_reviewed_on`. Fail closed when terms/permissions are unknown for production use.
- Always respect access/rate limits and published intended usage. **No CAPTCHA bypass, block evasion, private-session credential harvesting, proxy rotation to defeat anti-bot limits.**
- Example restriction: Travelpayouts Search API published terms explicitly prohibit combining its results with APIs of other flight metasearch services; do not add it to this aggregator without written permission and revised design.
- Source restrictions are a **provider gating concern**, not an excuse to remove modular architecture. An unavailable third-party integration remains a disabled adapter with reason; MVP may proceed with one compliant source.

## Mandatory error taxonomy

`network_timeout`, `http_rate_limited`, `auth_denied`, `provider_unavailable`, `schema_changed`, `partial_payload`, `invalid_currency`, `invalid_price`, `missing_segments`, `unsafe_fare`, `unsupported_query`, `terms_not_approved`, `unknown`.

Do not collapse `failed`, `unsupported`, `skipped` or `no eligible offers` into `succeeded_empty`.

## Required adapter test fixtures

- Success with 2 itineraries / 3 seller offers.
- Same itinerary from two providers with distinct price/brand.
- Codeshare and marketing/operating carrier mismatch.
- Missing flight number/timezone → unmatchable, no forced dedup.
- Currency conversion USD/IDR/JPY and price rounding.
- One provider returns no results vs one times out.
- Source response is truncated or `is_complete=false`.
- Basic economy cheapest vs main cabin; baggage unknown/required.
- Hidden-city flag true, false and unknown.
- Reprice increased/decreased/unavailable/brand changed/selector expired.
- Returned seller link generic vs exact.
- Duplicate quote across retries and repeated response handling.
- Restrictions forbid aggregation; adapter disabled and reason exposed.

**Gate:** do not advance provider-adapter work until the source is feasible, acceptable to use, and testable with a versioned fixture. Keep fake provider available for full app testing if real providers fail.

## Destination-discovery candidates (P7 research — unverified)

For the proposed Explore Anywhere feature ([01](01_PRODUCT_REQUIREMENTS_UX.md#proposed-feature-explore-anywhere-and-surprise-me-p7--proposed--not-started)).
**None of these is verified, approved or integrated.** Each needs the same P0-style probe
(actual response, terms, quotas, freshness) in P7.1 before any adapter work.

| Candidate | Possible use | Access / credentials | Known or expected limits | Native iPad (no server)? |
|---|---|---|---|---|
| Skiplagged (MCP, "anywhere"-style search if offered) | Destinations + indicative "from" prices from an origin | No auth for current detailed search; discovery tool not yet confirmed in the tool list | Personal-use terms (no commercial/redistribution); USD prices, display-only FX; hidden-city offers mixed in | Likely (plain HTTPS JSON-RPC), unproven |
| Travelpayouts / Aviasales price data | Cached cheapest prices by destination/month | API token, partner account | Cached/historical prices (age varies); published Search API rules prohibit combining with other metasearch APIs — data API terms must be checked separately; regional bias | Possible (HTTPS + token in app = key exposure risk) |
| swoop / Google Flights Explore | Destinations + prices from Google's Explore view | None; undocumented RPC | Undocumented, may break; ToS risk already accepted only for personal use; not known whether swoop exposes Explore | Unknown (swoop is Python; would need a Swift/Rust port) |
| Fli Explore | Same, via the Fli codebase/approach | None; public page | Not known whether Fli (pinned 881aee5) supports Explore; same Google block risk as Fli search | Possible via URLSession like Fli search, unproven |

Questions for every candidate: freshness/age signal, currency, geographic coverage, result
limits, rate limits, whether results can be shown next to other sources, and whether the
iPad can call it directly without exposing credentials.
