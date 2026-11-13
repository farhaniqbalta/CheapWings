# Fli probe — P5.06 spikes S1 (iPhone) and S3 (Swift off-device)

Question: does Google Flights return `ds:1` flight rows to **plain native `URLSession`**
(platform TLS, no Chrome impersonation)? See `docs/log/p5.05.md` §7. Fli is the must-have
provider, so S1 gates all native iOS work.

Throwaway spike code, not the app. Ports fli `881aee5` (MIT, Punit Arani): `tfs` encoder,
`ds:1` extraction, row/leg decoder, currency token — plus CheapWings' redirect, block and
cross-check rules from `backend/src/cheapwings/providers/fli.py`.

## Offline check (no network)

```sh
cd spikes/fli-probe && swift run fli-probe selftest     # Command Line Tools are enough
```

Checks: `tfs` bytes equal fli's for 3 routes, currency token, priced/fractional/unpriced
decode, null-minute times, date/airport/currency cross-check, redirect policy.

## S1 — physical iPhone (needs full Xcode, owner-approved live requests)

The app lives in `spikes/probe-app` (iPhone + iPad, iOS 17+) and also carries the S2 Rust
transport, so build `spikes/fli-wreq` first:

```sh
spikes/fli-wreq/build.sh                       # Rust → XCFramework + Swift bindings
cd spikes/probe-app && xcodegen generate        # brew install xcodegen
xcodebuild -project FliProbeApp.xcodeproj -scheme FliProbeApp -configuration Release \
  -destination 'id=<DEVICE_UDID>' -derivedDataPath build DEVELOPMENT_TEAM=<TEAM_ID> \
  -allowProvisioningUpdates build
xcrun devicectl device install app --device <DEVICE_UDID> build/Build/Products/Release-iphoneos/FliProbeApp.app
```

Free accounts: max 3 self-signed apps per device; trust the profile once in Settings ›
General › VPN & Device Management. Use the **physical device**, on the same network as the
Python baseline. Tap both offline checks first: `selftest OK` and `wreq client OK`.

Run protocol (stop rules are enforced by the app):

| Step | Transport / UA | Action |
|---|---|---|
| 1 | URLSession / `safariIPad` (iPad) or `safariIOS` (iPhone) | 3 single requests, ≥10 s apart, same query |
| 2 | URLSession / `chromeDesktop` | only if step 1 was `ROWLESS` (not blocked): 3 requests |
| 3 | Rust wreq Chrome (S2) | only if steps 1–2 did not pass and nothing was blocked: 3 requests |

- **PASS (S1 passes):** 3/3 `PASS` with URLSession. **S2 passes:** 3/3 `PASS` with wreq.
- **Stop for the day** at the first `BLOCKED_SORRY`, `BLOCKED_TRAFFIC`, `BLOCKED_REDIRECT`
  or `RATE_LIMITED`. The app latches and refuses more requests until relaunch. Do not retry
  from another network, VPN or identity; do not accept consent pages.
- Paste the **Share summaries** text back (one line per request: outcome, status, HTTP
  protocol, bytes, time, offer counts). It contains no provider payload.

## S3 — Swift off-device (macOS pre-check)

```sh
swift run fli-probe fetch --live CGK DPS 2026-12-15 IDR ID safariIOS
```

Same code on macOS `URLSession`. This is only a pre-check: Linux Swift uses a different
HTTP stack (FoundationNetworking/libcurl) and is not covered.

## What this does not do

No `wreq`/Rust (S2), no PyO3 (S4), no core skeleton (S5), no retries, no consent cookies,
no challenge handling, no proxy or identity rotation.
