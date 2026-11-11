# Swoop transport follow-up — 2026-11-11

Historical investigation. Final provider decision and implementation are in
[P4.11 Fli provider](p4.11.md); Viajante was not integrated.

## Base and scope

Owner requested restoring swoop after P4.10 merged. Fetched origin/main and
confirmed PR #4 merge `9a160d9` on top of P4.9 merge `a932900`. Created isolated
worktree `/tmp/cheapwings-swoop-fix`, branch `fix/swoop-transport`; left the original
P4.9 checkout's uncommitted Markdown changes and local runtime untouched.
The main-branch work log still described PR #4 as open; this follow-up corrects
that status using the actual merge commit.

## Current Fli experiment

Read current primary source/documentation from
[the Fli repository](https://github.com/punitarani/fli), source commit
`881aee5ff4321e81ea2157cb44be94ce6a21dc1b` (project version 0.10.0).
Installed its source and dependencies only in temporary virtual environment
`/tmp/cheapwings-fli-env`; production dependencies are unchanged.

Its current public-page encoder contains fields missing from swoop's older
TFS builder, so the earlier unsupported-page test did not validate current Fli.
The experiment used Fli's actual FlightSearchFilters, current encoder,
SearchFlights and decoder for one adult, economy, HND→CGK November 20, 2026,
ID point of sale and IDR currency. Disabled page/HTTP automatic retries, cleared
Fli's default pre-accepted SOCS cookie, and retained no payloads or selectors.

1. Current default Fli client (curl_cffi) ended with SearchConnectionError after
   11.182s. This is a connection failure, not evidence of an empty flight list.
2. Same current Fli encoder/search/parser with a standard HTTPX GET transport
   reached Google and received HTTP 302 from /travel/flights, redirecting to
   `www.google.com/sorry/index`, after 8.810s. Did not follow that redirect.

Stopped further live probes at the traffic-check response. No proxy/fingerprint
rotation, protection token creation/replay, consent-cookie fabrication, or
challenge handling was attempted. No failed job was reset and no live queue
work was created by these standalone diagnostics.

## Outcome and next step

Current Fli was actually evaluated; unlike the earlier old-builder test, this
provides evidence of explicit traffic-check blocking on the standard HTTP path.
It does not prove all browsers/networks or legitimate provider integrations fail.
Google's exact connection failure reason in the default client is unconfirmed.

Actual swoop retrieval is not restored. No unverified replacement adapter or
production fallback was deployed. Existing strict RPC error handling and cache
namespace v3 remain. Asked the owner whether the same route/date returns fares
or a traffic-check/CAPTCHA in their normal browser. A working permitted transport
must be demonstrated before implementation and capability/normalization tests.
No application code changed, so no backend regression rerun was necessary.

## Owner-requested direct RPC and swoop documentation check

Owner reports that a normal Google Flights search returns results, then explicitly
requested a direct Google API query followed by swoop documentation review.
Executed one direct POST to the undocumented GetShoppingResults endpoint using
the installed SDK's request builder, HND→CGK November 20, economy, one adult,
basic economy included, ID point of sale. Standard HTTPX client; no retries or
redirect following. Result: HTTP 302 after 9.387s, 477 response bytes, no flight
payload processed. This direct probe did not record the Location header, so its
redirect destination is unconfirmed; do not label it /sorry based on the
separate earlier public-page experiment. No raw response was persisted.

Reviewed swoop's official README, MIGRATION.md, releases and
[issue #30](https://github.com/saraswatayu/swoop/issues/30). The README still
describes undocumented RPC transport. Release 0.7.0 (already installed) improves
structured upstream error reporting; it does not document a recovery transport.
The migration guide says transport.retries applies to HTTP 429, not upstream
RPC errors. The June 2026 issue records error-13 rejection recovering without
client changes and later recurring. This historical incident shows that error
13 alone cannot prove a permanent protocol change; it does not establish the
reason or expected recovery time for the present failure. No current documented
client setting or upgrade was found that demonstrably restores our queries.

Browser results establish route/date inventory exists, while standalone client
access remains unsuccessful. No production code or provider settings changed
in this follow-up; actual fare retrieval is still unresolved.

## Swoop-only reproduction and historical boundary

Owner explicitly requested returning to a minimal swoop implementation and
tracing where it stopped responding. No browser or replacement-library work
was pursued in this step. Read the P4.8/P4.9 work logs, provider commit history,
and persisted swoop work-item statuses in the existing local database.

| Observation | UTC, 2026-11-11 | Jakarta | Evidence |
|---|---|---|---|
| Last confirmed live-result batch | 02:39:27–02:39:31 | 09:39 | MEL→CGK, Dec 1–31: 31 succeeded_results/live, 311 offers |
| First later suspicious all-empty batch | 06:57:40–06:57:48 | 13:57 | MEL→CGK, Nov 11–30: 20 succeeded_empty/live |
| Later sandbox failure batch | 07:09:14–07:09:29 | 14:09 | swoop 31 provider_unavailable; DNS sandbox cause documented previously |
| Guard committed, ab5193f | 10:13:07 | 17:13 | Strict RPC validation and cache namespace v3 |

The dates differ between the last successful and first suspicious batches.
Their historical payloads were not retained, so neither the precise transition
time nor those empty responses' exact error envelopes can be proven. The
suspicious empty batch predates both the sandbox-failure batch and the guard.
P4.8 also had clean swoop C1/C2 results; last follow-up call in its detailed
table was Nov 10 17:13:27 UTC (Nov 11 00:13 Jakarta), before the above batches.
The successful P4.9 batches already used bounded C3 execution; concurrency alone
does not explain later standalone failures. SDK version remains 0.7.0.

Two one-shot SDK-only calls, no CheapWings imports/worker/cache/normalization:

- MEL→DPS, Dec 18, US point of sale, basic included: SDK reported zero results,
  is_complete=True, 0.846s. This is not validated empty inventory because the
  installed SDK can swallow short error envelopes. No fares returned.
- MEL→CGK, Dec 1, ID point of sale, basic included: SwoopRateLimitError, HTTP
  429, 8.473s. This is a genuine throttle response. Stopped immediately; no
  automatic retries, alternate identities, or subsequent live requests.

The latter uses a route/date and preferences from the last confirmed live batch.
Added opt-in `scripts/benchmarks/swoop_minimal.py` to reproduce this with the
public swoop.search API, one request, concurrency one and retries=0. Prints only
SDK version, request metadata, counts, up to three price/currency pairs and
sanitized exception class/status. No payloads/selectors/credentials persisted.

Recorded the SDK adapter's existing conservative 120s cooldown into shared
provider state, through Repository.record_provider_feedback, so the ordinary
worker also respects this externally observed throttle. Deadline recorded:
2026-11-11 12:17:00.395 UTC. No jobs reset, cancelled or created by the experiment.
A later recovery check must respect cooldown; expiry alone does not trigger one.
No production code changes or retrieval success claimed.

## Viajante standalone evaluation — 2026-11-11

Owner requested checking Viajante and verifying it with a simple implementation.
Identified [felipebasurto/viajante](https://github.com/felipebasurto/viajante) and
read its official usage guide and source. Tested repository source commit
`377adfd3d9504d62bf26543eaf62c62bdd2356a5`, package version 1.5.6, installed
only in `/tmp/cheapwings-viajante-env`. Production dependencies remain unchanged.

Used public Python API `search_flights([FlightQuery(...)], fetch="sweep")`,
one HND→CGK query for November 20, 2026, one adult/economy, at most two stops,
ID point of sale, IDR requested currency, top three offers, 30s deadline.
Outer library attempts limited to one; library transport may replay a connection
failure once. No browser fallback, proxy rotation or challenge workaround.
Previously recorded Google cooldown had expired hours before these calls.

| Invocation | Status | Elapsed | Raw / eligible / returned offers |
|---|---|---:|---:|
| First | error: fetch_failed | 23.176s | none |
| Diagnostic follow-up, same query | ok | 11.165s | 22 / 22 / 3 |

Successful result explicitly returned currency IDR and backend sweep. Samples:

| Airline | Price, IDR | Stops |
|---|---:|---:|
| Scoot | 6,144,602 | 1 |
| Scoot | 6,999,158 | 1 |
| Korean Air | 10,215,935 | 1 |

These are observed shopping quotes, not guaranteed booking prices. The initial
fetch_failed report did not expose an HTTP/RPC status or precise underlying
transport cause in the retained sanitized output; do not call it rate limiting
or an empty inventory. The second invocation changed only diagnostic output,
not route/date/transport/identity settings. No third live invocation was made.
No SDK payloads, selectors, booking tokens, cookies or credentials were retained
in the repository. The temporary SDK state directory contained no files when
inspected after testing.

Added `scripts/benchmarks/viajante_minimal.py`: opt-in, standalone, HTTP sweep
only, one query per invocation, summaries/sample prices only. Ruff/format and
syntax checks cover the artifact; no production code changed. Official docs
export FlightQuery/search_flights and distinguish blocked/markup errors from
true no-inventory responses. Important integration differences: max_stops is
0/1/2 (this control was <=2, not CheapWings any-stops); basic-economy exclusion
is refused because the page cannot prove it. Do not silently drop these limits.

Outcome: **Viajante demonstrably retrieved real priced offers in this environment
on one of two invocations.** It is a viable candidate for further testing, not
a demonstrated reliable replacement or evidence that swoop itself recovered.
No caching, repricing, concurrency or total batch-throughput experiment was
performed. Existing CheapWings runtime was not changed or restarted.
