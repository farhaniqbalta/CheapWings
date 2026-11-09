# Provider Proof-of-Concept Report (P0)

**Date:** 2026-11-09
**Route/date used for all live probes:** MEL → DPS, departing 2026-12-16, one-way, 1 adult, economy (the same non-live example fixture route named in `docs/README.md`). All prices below are real numbers returned by the providers at probe time — they are **not fabricated**, but they are a snapshot and must not be treated as current or bookable.
**Environment:** macOS, Python 3.12.16 (installed via Homebrew for this probe), `mcp` SDK 2.3.0, `swoop-flights` 0.7.0 (installed from PyPI into a throwaway venv `.venv_probe/`, not committed).
**Redacted fixtures:** `contracts/fixtures/provider/skiplagged_probe_*.json`, `contracts/fixtures/provider/swoop_probe_*.json`. Opaque `selector` and `booking_url` values were replaced with `<redacted-... len=N>` placeholders before committing, per `docs/07_TESTING_AND_OPERATIONS.md`'s evidence-retention rule. Raw unredacted responses were not persisted outside this session.
**Exact probe commands:**
```bash
source .venv_probe/bin/activate
python scripts/provider_probe_skiplagged.py            # tools/list only
python scripts/provider_probe_skiplagged.py --search --faq   # + 1 search call + 4 FAQ queries
python scripts/provider_probe_swoop.py                  # 1 search + 1 price_selector + 1 basic-economy search
```
Each probe script makes a small, fixed number of calls (no loops, no retries beyond library defaults) and was run once per variant in this session — low-volume by construction.

**Not performed in this session:** manual side-by-side comparison against the Skiplagged website or Google Flights in a browser. This environment has no browser/display available to the agent. This is a real gap in the P0 checklist (`docs/03`'s "attempt a low-cost comparison with the supplier/airline website") and should be done manually by the owner before relying on either provider for real money decisions. Treat the manual-comparison item below as **unverified**, not passed.

---

## Skiplagged remote MCP

**Endpoint:** `https://mcp.skiplagged.com/mcp` (no auth — confirmed, connected without credentials)
**Source:** https://skiplagged.github.io/mcp/ (docs), `skiplagged.com/terms` (site-wide terms)

### Claims vs observed

| Claim (docs) | Observed (this session) |
|---|---|
| No authentication required | Confirmed — `ClientSession.initialize()` succeeded with no credentials. |
| Tools include flight/calendar/hotel/car search | `tools/list` returned exactly 10 tools: `sk_flights_search`, `sk_destinations_anywhere`, `sk_flex_departure_calendar`, `sk_flex_return_calendar`, `sk_hotels_search`, `sk_cars_search`, `sk_hotel_details`, `sk_faq_search`, `sk_resolve_location`, `sk_resolve_iata`. **No repricing/price-check/selector tool of any kind exists.** This is a hard fact, not an inference: repricing is not a Skiplagged MCP capability. `ProviderCapabilities.exact_reprice=False` for Skiplagged, confirmed. |
| Prices are approximate in non-USD currencies | Confirmed in output: `pricing.approximate=true`, `pricing.rate`, `pricing.rateAsOf`, and each flight's `price.usdAmount` (source-of-truth) alongside `price.amount` in the requested currency. Our domain layer must store `usdAmount` as the authoritative source amount and treat the IDR figure as a converted display value — matches `docs/03`'s FX-preservation rule. |
| Hidden-city fares included by default | Confirmed: `includeHiddenCity` input defaults to `true`. We can explicitly request `includeHiddenCity: false` (and `includeVirtualInterlining: false`) to exclude them at the query level — this is **better than assumed**: Skiplagged lets the caller opt out, so we don't have to post-filter unclassified candidates. Each `FlightCard.attributes` array also carries a classification tag (`"standard"`, `"nonstop"` observed, `"hidden-city"` not observed in this run because it was excluded by request — not confirmed what the exact string value is; needs one more probe call with `includeHiddenCity: true` before implementation, to pin the exact attribute string(s) used for hidden-city/self-transfer classification). |
| Site terms prohibit scraping, commercial use, redistribution | Confirmed via `skiplagged.com/terms`: explicit bans on "robot, spider, scraper or other automated means," any "commercial or non-personal purpose," and "distribute, transmit, display, ... re-sell any information ... obtained from this Site." **The MCP docs page does not restate or override these terms, and `sk_faq_search` queried 4 times for caching/aggregation/commercial/redistribution policy returned zero matching FAQ articles for 3 of 4 queries** — i.e., no explicit MCP-specific permission was found anywhere reachable in this session. |

### Fields present / absent (for canonical domain mapping)

- **Present per result:** `airlines` (string, may be multi-carrier comma-joined — not itemized per segment), `departure`/`arrival` (airport + local ISO datetime with offset — only first-origin/last-destination, not per-leg), `duration`, `layovers` (count only), `price.{amount,currency,usdAmount}`, `deepLink` (public search URL + `#trip=<carrier><flightnum>` fragment, not a signed URL), `attributes` (string tags).
- **Absent:** no structured per-segment array (operating vs marketing carrier, individual flight numbers, intermediate airports) for itineraries with `layovers > 0`; no fare family/brand; no seller/OTA name; no baggage allowance; no `is_estimate`/`is_complete`/source-timestamp field in the output schema (only `pagination.totalAvailable/currentlyShowing` for truncation signal); no reprice/selector handle.
- **Consequence for `docs/03`'s matching algorithm:** nonstop Skiplagged results have just enough identity (single flight number embedded only in the `deepLink` fragment, not a typed field) to be a usable but weak `exact_segments` candidate; any itinerary with `layovers ≥ 1` lacks typed per-segment identity and **must** be treated as `insufficient_identity` under the conservative-matching rule — we cannot safely dedupe/merge connecting Skiplagged itineraries against another provider's segments.

### Live sample (redacted selector/links kept short; full in fixture)

MEL→DPS 2026-12-16, 5 cheapest-by-value, `includeHiddenCity=false`, IDR: nonstop fares from Garuda Indonesia (IDR 4,907,458 / USD 271), Jetstar (×2), Malindo Air, TransNusa — see `contracts/fixtures/provider/skiplagged_probe_20261109T123430Z.json` for the full structured payload (`search_structured_content`).

### Verdict: **CONDITIONAL GO**

Usable for a personal, low-volume, single-operator deployment: the MCP server is explicitly built and marketed for exactly this kind of AI-agent/no-auth consumption (`utm_medium=ai` tracking params are a strong signal of intended use), it is reachable with zero friction, and it returns real, usable flight data with an explicit hidden-city opt-out. **It is NOT cleared for redisplaying results to other users, caching beyond the duration of a single job, or any commercial use** — the main site's written terms prohibit exactly that, and nothing MCP-specific grants an exception. Concretely: `permitted_to_aggregate=unknown→treat as false for multi-user/public deployment`, `can_cache=short-TTL-only (job lifetime)`, `attribution_required=yes (per their own utm/branding pattern, keep deep links intact)`. Enable only as `enabled=true` in a **single-owner, non-redistributed, personal-use** configuration; do not enable for a publicly shared instance without written permission from Skiplagged. No exact-repricing capability exists — all Skiplagged offers are `recent_search` or `indicative` at best, never `repriced_exact`.

---

## swoop (reverse-engineered Google Flights RPC)

**Package:** `swoop-flights` 0.7.0 (PyPI), MIT license
**Source:** https://github.com/saraswatayu/swoop

### Claims vs observed

| Claim (README) | Observed (this session) |
|---|---|
| Real prices, no API key | Confirmed: `swoop.search("MEL","DPS","2026-12-16", cabin="economy", include_basic_economy=False)` returned 11 priced `TripOption`s with `is_complete=True`, no credentials needed. |
| `price_selector()` gives exact fare + booking options | Confirmed: took the top result's `selector`, called `price_selector()`, got `PriceResult` with `price=7,764,811 IDR`, `is_estimate=True`, `is_basic_economy=False`, and 1+ `booking_options` entries with `seller_name="Jetabroad"`, `fare_family="basic"`, `is_basic=True`, `rebookability_signal="restricted"`, and a Google-redirect `booking_url`. **Important nuance confirmed live:** the top-level `PriceResult.is_basic_economy` can disagree with an individual `booking_options[i].is_basic` — the top-level field describes the priced itinerary/selector as requested, while each booking option is its own seller/fare combination. Our matching layer must key offers off `booking_options[]`, not assume the top-level flag applies to every seller shown. |
| Full segment-level itinerary detail | Confirmed and **materially richer than Skiplagged**: each `TripOption.legs[].itinerary.segments[]` has `airline`, `flight_number`, `operator` (separate marketing/operating field, empty string observed = same-carrier operated), `aircraft`, per-segment local departure/arrival date+time, `travel_time`, amenities, `co2_grams`. This satisfies `docs/03`'s itinerary-identity requirement (ordered segments with flight numbers) for both nonstop and connecting itineraries — unlike Skiplagged. |
| `include_basic_economy` toggle changes results | Confirmed: with the flag off, cheapest observed was ~7.76M IDR (from the selector probed); with it on, `cheapest_price=4,891,694 IDR` across the same 11-result response (`is_complete=True` both times) — a materially lower floor, as expected. |
| Hidden-city detection | **Not present anywhere in the library.** No field, no flag, no mention in README or observed output. We cannot get a hidden-city signal from swoop; every swoop offer must be recorded `hidden_city=unknown` (not `no`) per the three-valued enum rule, unless we later add independent detection logic. In practice Google Flights itself does not typically sell overt hidden-city fares the way Skiplagged does, which lowers — but does not eliminate — the practical risk; this is an assumption, not a proof. |
| Google rate-limits aggressively; use conservative retries | Not stress-tested (by design — no intentional rate-limit probing). 3 live calls (search ×2, price_selector ×1) in this session all succeeded on first attempt with no 429s. |

### Legal/compliance note (the real risk for swoop)

The `swoop-flights` package itself is MIT-licensed with no usage restriction on the code. The risk is **not** the library's license — it's that the library calls Google's undocumented, internal `FlightsFrontendService` RPC with TLS fingerprint impersonation to look like a browser, which is the kind of automated access Google's general Terms of Service typically restrict for unauthorized clients (standard clause across Google products; this session did not fetch and quote Google's specific Flights ToS text, so treat this as a known category of risk, not a verified quote). This is a materially different risk profile than Skiplagged's MCP server, which is a product Skiplagged built and published *for* this kind of use. swoop's README itself only disclaims "not affiliated with Google" and warns the RPC "can change without notice" — it does not claim legal clearance.

### Verdict: **CONDITIONAL GO**

Functionally the stronger provider — full segment identity, basic-economy toggle, seller-level booking options, and an actual (if estimate-flagged) repricing call via `price_selector()`/`check_price()`. Enable for low-volume personal use (`enabled=true`, bounded executor, 1–2 concurrent calls, generous backoff per the README's own guidance) with `exact_reprice` capability wired to `price_selector`, but mark **`price_status` from swoop as `repriced_exact` only when `is_estimate=False`** — the single live call in this session returned `is_estimate=True`, so even "repriced" swoop quotes default to a lower-confidence label until proven otherwise on a given itinerary. Legal risk (unauthorized automated access to Google's internal RPC) is real and unresolved by this probe; it is a judgment call for the owner whether to accept that risk for a personal/low-volume tool — flagging per `docs/06`'s escalation rule rather than deciding unilaterally that it's fine.

---

## Combined P0 gate outcome

**At least one provider (both, conditionally) exposes a usable, real, low-volume-compliant one-way search for the target route/date class.** Gate passed — proceed to P1 (domain + fake-provider slice) is unblocked. Neither provider reaches an unconditional GO:

| Provider | Verdict | Blocking condition before wider/public use |
|---|---|---|
| Skiplagged MCP | CONDITIONAL GO | Site terms ban commercial use/redistribution/scraping; no MCP-specific permission found. Personal single-owner use only. |
| swoop | CONDITIONAL GO | Legal status of unauthorized Google RPC access unresolved; owner risk acceptance needed for anything beyond personal/low-volume use. |

### Decisions NOT made here (owner-level, per `docs/06` stop/escalation rule)

1. Whether personal, non-redistributed, single-owner use of Skiplagged MCP is acceptable despite the site-wide commercial/redistribution ban (the MCP server's own design suggests Skiplagged intends this, but nothing in writing says so).
2. Whether swoop's reliance on undocumented Google RPC access is an acceptable ongoing legal risk for this project, even at low volume.

Both are exactly the kind of **"a proposed feature changes non-negotiable scope" / fundamental incompatibility** case `docs/06_IMPLEMENTATION_CHECKPOINTS.md` says to stop and flag rather than resolve unilaterally — they're flagged here, not decided.

### Follow-up probe items

- Ran one additional `sk_flights_search` call with `includeHiddenCity: true, includeVirtualInterlining: true, limit: 15` for MEL→DPS 2026-12-16 to pin the exact hidden-city `attributes` tag string. **Inconclusive**: the only tags observed across all 15 results were `"standard"`, `"nonstop"`, `"one-stop"` — no hidden-city or virtual-interlining fare happened to rank in the top 15 for this specific route/date, so the exact tag string for those classifications is still unconfirmed. Needs a route/date known to surface a cheap hidden-city fare (not guessed/fabricated here) before the adapter can safely map `attributes` to our `hidden_city` enum; until then, treat any Skiplagged result as `hidden_city=unknown` whenever `includeHiddenCity=true` is used, and only trust `hidden_city=no` when the query itself was sent with `includeHiddenCity=false` (as in the main probe above).
- Manual browser-based price comparison against skiplagged.com and Google Flights for the same route/date — still not performed (no browser available to the agent in this session).
