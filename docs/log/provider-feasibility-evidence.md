# Provider feasibility evidence

> Historical WORK_LOG archive (2026-11-10). Evidence and decisions remain as recorded; navigation links and whitespace may be normalized. Current status and approvals: [WORK_LOG.md](../../WORK_LOG.md).

## Provider feasibility evidence

Consolidated in full from the former standalone provider report at the owner's
request. P0 findings below are historical observations from 2026-11-09, followed
by the P3 production-adapter canary. The provider decision ledger above governs
current owner-accepted personal-use scope; earlier conditional/unresolved wording
is retained as historical evidence and does not reopen those decisions.

Evidence corrections already established during implementation: the P0 swoop
search contained 11 candidates, **10 priced and 1 unpriced**, despite the original
"11 priced" wording below. Production Skiplagged normalization conservatively
keeps even nonstop cards unmatched because operating-carrier identity is absent.

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

### Skiplagged remote MCP

**Endpoint:** `https://mcp.skiplagged.com/mcp` (no auth — confirmed, connected without credentials)
**Source:** https://skiplagged.github.io/mcp/ (docs), `skiplagged.com/terms` (site-wide terms)

#### Claims vs observed

| Claim (docs) | Observed (this session) |
|---|---|
| No authentication required | Confirmed — `ClientSession.initialize()` succeeded with no credentials. |
| Tools include flight/calendar/hotel/car search | `tools/list` returned exactly 10 tools: `sk_flights_search`, `sk_destinations_anywhere`, `sk_flex_departure_calendar`, `sk_flex_return_calendar`, `sk_hotels_search`, `sk_cars_search`, `sk_hotel_details`, `sk_faq_search`, `sk_resolve_location`, `sk_resolve_iata`. **No repricing/price-check/selector tool of any kind exists.** This is a hard fact, not an inference: repricing is not a Skiplagged MCP capability. `ProviderCapabilities.exact_reprice=False` for Skiplagged, confirmed. |
| Prices are approximate in non-USD currencies | Confirmed in output: `pricing.approximate=true`, `pricing.rate`, `pricing.rateAsOf`, and each flight's `price.usdAmount` (source-of-truth) alongside `price.amount` in the requested currency. Our domain layer must store `usdAmount` as the authoritative source amount and treat the IDR figure as a converted display value — matches `docs/03`'s FX-preservation rule. |
| Hidden-city fares included by default | Confirmed: `includeHiddenCity` input defaults to `true`. We can explicitly request `includeHiddenCity: false` (and `includeVirtualInterlining: false`) to exclude them at the query level — this is **better than assumed**: Skiplagged lets the caller opt out, so we don't have to post-filter unclassified candidates. Each `FlightCard.attributes` array also carries a classification tag (`"standard"`, `"nonstop"` observed, `"hidden-city"` not observed in this run because it was excluded by request — not confirmed what the exact string value is; needs one more probe call with `includeHiddenCity: true` before implementation, to pin the exact attribute string(s) used for hidden-city/self-transfer classification). |
| Site terms prohibit scraping, commercial use, redistribution | Confirmed via `skiplagged.com/terms`: explicit bans on "robot, spider, scraper or other automated means," any "commercial or non-personal purpose," and "distribute, transmit, display, ... re-sell any information ... obtained from this Site." **The MCP docs page does not restate or override these terms, and `sk_faq_search` queried 4 times for caching/aggregation/commercial/redistribution policy returned zero matching FAQ articles for 3 of 4 queries** — i.e., no explicit MCP-specific permission was found anywhere reachable in this session. |

#### Fields present / absent (for canonical domain mapping)

- **Present per result:** `airlines` (string, may be multi-carrier comma-joined — not itemized per segment), `departure`/`arrival` (airport + local ISO datetime with offset — only first-origin/last-destination, not per-leg), `duration`, `layovers` (count only), `price.{amount,currency,usdAmount}`, `deepLink` (public search URL + `#trip=<carrier><flightnum>` fragment, not a signed URL), `attributes` (string tags).
- **Absent:** no structured per-segment array (operating vs marketing carrier, individual flight numbers, intermediate airports) for itineraries with `layovers > 0`; no fare family/brand; no seller/OTA name; no baggage allowance; no `is_estimate`/`is_complete`/source-timestamp field in the output schema (only `pagination.totalAvailable/currentlyShowing` for truncation signal); no reprice/selector handle.
- **Consequence for `docs/03`'s matching algorithm:** nonstop Skiplagged results have just enough identity (single flight number embedded only in the `deepLink` fragment, not a typed field) to be a usable but weak `exact_segments` candidate; any itinerary with `layovers ≥ 1` lacks typed per-segment identity and **must** be treated as `insufficient_identity` under the conservative-matching rule — we cannot safely dedupe/merge connecting Skiplagged itineraries against another provider's segments.

#### Live sample (redacted selector/links kept short; full in fixture)

MEL→DPS 2026-12-16, 5 cheapest-by-value, `includeHiddenCity=false`, IDR: nonstop fares from Garuda Indonesia (IDR 4,907,458 / USD 271), Jetstar (×2), Malindo Air, TransNusa — see `contracts/fixtures/provider/skiplagged_probe_20261109T123430Z.json` for the full structured payload (`search_structured_content`).

#### Verdict: **CONDITIONAL GO**

Usable for a personal, low-volume, single-operator deployment: the MCP server is explicitly built and marketed for exactly this kind of AI-agent/no-auth consumption (`utm_medium=ai` tracking params are a strong signal of intended use), it is reachable with zero friction, and it returns real, usable flight data with an explicit hidden-city opt-out. **It is NOT cleared for redisplaying results to other users, caching beyond the duration of a single job, or any commercial use** — the main site's written terms prohibit exactly that, and nothing MCP-specific grants an exception. Concretely: `permitted_to_aggregate=unknown→treat as false for multi-user/public deployment`, `can_cache=short-TTL-only (job lifetime)`, `attribution_required=yes (per their own utm/branding pattern, keep deep links intact)`. Enable only as `enabled=true` in a **single-owner, non-redistributed, personal-use** configuration; do not enable for a publicly shared instance without written permission from Skiplagged. No exact-repricing capability exists — all Skiplagged offers are `recent_search` or `indicative` at best, never `repriced_exact`.

---

### swoop (reverse-engineered Google Flights RPC)

**Package:** `swoop-flights` 0.7.0 (PyPI), MIT license
**Source:** https://github.com/saraswatayu/swoop

#### Claims vs observed

| Claim (README) | Observed (this session) |
|---|---|
| Real prices, no API key | Confirmed: `swoop.search("MEL","DPS","2026-12-16", cabin="economy", include_basic_economy=False)` returned 11 priced `TripOption`s with `is_complete=True`, no credentials needed. |
| `price_selector()` gives exact fare + booking options | Confirmed: took the top result's `selector`, called `price_selector()`, got `PriceResult` with `price=7,764,811 IDR`, `is_estimate=True`, `is_basic_economy=False`, and 1+ `booking_options` entries with `seller_name="Jetabroad"`, `fare_family="basic"`, `is_basic=True`, `rebookability_signal="restricted"`, and a Google-redirect `booking_url`. **Important nuance confirmed live:** the top-level `PriceResult.is_basic_economy` can disagree with an individual `booking_options[i].is_basic` — the top-level field describes the priced itinerary/selector as requested, while each booking option is its own seller/fare combination. Our matching layer must key offers off `booking_options[]`, not assume the top-level flag applies to every seller shown. |
| Full segment-level itinerary detail | Confirmed and **materially richer than Skiplagged**: each `TripOption.legs[].itinerary.segments[]` has `airline`, `flight_number`, `operator` (separate marketing/operating field, empty string observed = same-carrier operated), `aircraft`, per-segment local departure/arrival date+time, `travel_time`, amenities, `co2_grams`. This satisfies `docs/03`'s itinerary-identity requirement (ordered segments with flight numbers) for both nonstop and connecting itineraries — unlike Skiplagged. |
| `include_basic_economy` toggle changes results | Confirmed: with the flag off, cheapest observed was ~7.76M IDR (from the selector probed); with it on, `cheapest_price=4,891,694 IDR` across the same 11-result response (`is_complete=True` both times) — a materially lower floor, as expected. |
| Hidden-city detection | **Not present anywhere in the library.** No field, no flag, no mention in README or observed output. We cannot get a hidden-city signal from swoop; every swoop offer must be recorded `hidden_city=unknown` (not `no`) per the three-valued enum rule, unless we later add independent detection logic. In practice Google Flights itself does not typically sell overt hidden-city fares the way Skiplagged does, which lowers — but does not eliminate — the practical risk; this is an assumption, not a proof. |
| Google rate-limits aggressively; use conservative retries | Not stress-tested (by design — no intentional rate-limit probing). 3 live calls (search ×2, price_selector ×1) in this session all succeeded on first attempt with no 429s. |

#### Legal/compliance note (the real risk for swoop)

The `swoop-flights` package itself is MIT-licensed with no usage restriction on the code. The risk is **not** the library's license — it's that the library calls Google's undocumented, internal `FlightsFrontendService` RPC with TLS fingerprint impersonation to look like a browser, which is the kind of automated access Google's general Terms of Service typically restrict for unauthorized clients (standard clause across Google products; this session did not fetch and quote Google's specific Flights ToS text, so treat this as a known category of risk, not a verified quote). This is a materially different risk profile than Skiplagged's MCP server, which is a product Skiplagged built and published *for* this kind of use. swoop's README itself only disclaims "not affiliated with Google" and warns the RPC "can change without notice" — it does not claim legal clearance.

#### Verdict: **CONDITIONAL GO**

Functionally the stronger provider — full segment identity, basic-economy toggle, seller-level booking options, and an actual (if estimate-flagged) repricing call via `price_selector()`/`check_price()`. Enable for low-volume personal use (`enabled=true`, bounded executor, 1–2 concurrent calls, generous backoff per the README's own guidance) with `exact_reprice` capability wired to `price_selector`, but mark **`price_status` from swoop as `repriced_exact` only when `is_estimate=False`** — the single live call in this session returned `is_estimate=True`, so even "repriced" swoop quotes default to a lower-confidence label until proven otherwise on a given itinerary. Legal risk (unauthorized automated access to Google's internal RPC) is real and unresolved by this probe; it is a judgment call for the owner whether to accept that risk for a personal/low-volume tool — flagging per `docs/06`'s escalation rule rather than deciding unilaterally that it's fine.

---

### Combined P0 gate outcome

**At least one provider (both, conditionally) exposes a usable, real, low-volume-compliant one-way search for the target route/date class.** Gate passed — proceed to P1 (domain + fake-provider slice) is unblocked. Neither provider reaches an unconditional GO:

| Provider | Verdict | Condition for wider/public use |
|---|---|---|
| Skiplagged MCP | **GO** — personal/single-owner use (owner-accepted 2026-11-09) | Site terms ban commercial use/redistribution/scraping; no MCP-specific permission found. Must revisit (seek written permission) before any public/multi-user launch. |
| swoop | **GO** — personal/low-volume use (owner-accepted 2026-11-09) | Legal status of unauthorized Google RPC access remains unresolved in the abstract; owner explicitly accepted this risk for a personal project. Must revisit if this ever scales or becomes commercial. |

#### Owner decisions (resolved 2026-11-09, per `docs/06` stop/escalation rule)

These were flagged as fundamental-incompatibility-style questions rather than resolved unilaterally. Owner's answers:

1. **Skiplagged, personal/non-redistributed use despite the site-wide commercial/redistribution ban:** accepted, conditioned on the project staying personal/non-redistributed. Confirmed understanding: fine to run for yourself (and people you personally let use it), not fine to turn into a public signup product without separately asking Skiplagged.
2. **swoop's reliance on undocumented Google RPC access:** accepted for a personal, low-volume project after the legal-risk tradeoff was explained (contract-violation / blocking risk, not realistic legal-action risk at hobby scale). Revisit before any scale-up or commercialization.

Both acceptances are personal-project-scoped. `provider_registry.permitted_to_aggregate` and `can_cache` should still default to the conservative personal-use settings described per-provider above — the owner's acceptance is not a blanket "treat as a licensed commercial API."

#### Follow-up probe items

- Ran one additional `sk_flights_search` call with `includeHiddenCity: true, includeVirtualInterlining: true, limit: 15` for MEL→DPS 2026-12-16 to pin the exact hidden-city `attributes` tag string. **Inconclusive**: the only tags observed across all 15 results were `"standard"`, `"nonstop"`, `"one-stop"` — no hidden-city or virtual-interlining fare happened to rank in the top 15 for this specific route/date, so the exact tag string for those classifications is still unconfirmed. Needs a route/date known to surface a cheap hidden-city fare (not guessed/fabricated here) before the adapter can safely map `attributes` to our `hidden_city` enum; until then, treat any Skiplagged result as `hidden_city=unknown` whenever `includeHiddenCity=true` is used, and only trust `hidden_city=no` when the query itself was sent with `includeHiddenCity=false` (as in the main probe above).
- Manual browser-based price comparison against skiplagged.com and Google Flights for the same route/date — still not performed (no browser available to the agent in this session).

---

### P3 live canary (2026-11-09, addendum)

Where the P0 section above called the SDKs/MCP server directly with ad hoc
scripts, this canary runs the **actual production adapter classes**
(`cheapwings.providers.skiplagged.SkiplaggedProvider`,
`cheapwings.providers.swoop.SwoopProvider`) against live endpoints — the
real normalization/error-handling code path the worker uses, not a probe
shim. Same route/date as P0 (MEL→DPS, 2026-12-16) for comparability.
`mcp`==2.3.0, `swoop-flights`==0.7.0, `airportsdata`==20261103 (the pinned
`backend[live]` extra). One search call per provider, one `reprice()` call
on swoop's top result — still low-volume, still a single run.

**Command:** `python scripts/p3_live_canary.py` (script redacts nothing by
itself — its raw JSON output contains swoop's opaque selector and was
**not committed**; only this redacted summary is kept).

**Skiplagged:** `SkiplaggedProvider.search()` returned 20 normalized offers,
status `succeeded_results`, no adapter exceptions. Sample offer: original
USD 272 → comparable IDR 4,925,566 via a preserved `FXSnapshot` (rate
18108.7, matches the live rate at probe time), `hidden_city=no` (query sent
`includeHiddenCity=false`), `checked_bag=unknown`, `price_status=indicative`,
`is_estimate=True`, link correctly scoped to `generic_search` and validated
`https://skiplagged.com/...`. No fabricated seller/fare-family — both
`null` since the source never provides them, exactly per the P0 findings.

**swoop:** `SwoopProvider.search()` returned 10 priced + **1 unpriced**
candidate — the adapter's explicit `unpriced_candidate_count` correctly
caught the same no-price/no-currency quirk documented in the P0 section,
on a fresh live call, not just the frozen fixture. `SwoopProvider.reprice()`
on the top result succeeded: real seller `"Jetstar"`, `is_estimate=False`,
opaque `provider_quote_handle` populated (never a link — swoop reprice
offers don't expose a direct URL). `exact_product_match=False` here because
the *search*-stage offer never carries seller/fare_family (swoop doesn't
expose that pre-reprice), so the adapter's independent-field match
intentionally cannot succeed from a bare search→reprice chain with no
in-between verification step — this is the conservative behavior
`docs/03`'s matching rule requires, not a bug.

**Verdict:** both adapters behave correctly against live data, consistent
with the P0 findings and the existing offline test suite (which replays
these same P0 fixtures through the identical adapter code in
`backend/tests/integration/test_p3.py::test_recorded_real_adapters_api_summary_fx_and_expiry`).
No new GO/NO-GO decision needed — this confirms the already-accepted
personal-use GO for both providers extends to the real adapter
implementation, not just the raw SDK.

### Reporting consolidation (2026-11-09)
- Owner explicitly required all reports to live in WORK_LOG.md. Merged the complete P0 provider evidence and P3 canary addendum here, removed the standalone report, and updated active specifications, bootstrap instructions, README links and the canary docstring. No provider calls or application behavior changes.
- Updated P4.5 handoff instructions: the UI/UX agent must append its design-return findings here rather than create another report. Release and test summaries likewise belong here. Static UI/UX prompts/integration specifications remain separate assignment artifacts, as requested previously. Historical V4 reference left untouched.
