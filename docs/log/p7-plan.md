# P7 Discover — Readiness, Feasibility and Shared Rust Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Take P7 from "proposed" to a provider go/no-go decision, then (only on go) ship the pure Rust `select_discovery_plan` with PyO3 and UniFFI bindings, proven identical on web and iPad by one shared fixture.

**Architecture:** P7.0/P7.1 are docs plus one owner-approved, low-volume probe. P7.2/P7.3 add `core/cheapwings-core/src/discovery.rs`, which turns priced observations into an explicit, capped `Vec<RouteDate>` (cheapest observation per destination, then top N). It reuses `planning`'s airport/date validation and `money::fx_convert`. PyO3 uses JSON in and out (the `skiplagged_parse` pattern); UniFFI mirrors the records. No runtime, storage or UI changes: P7.4–P7.6 get their own plan after the P7.1 go.

**Tech Stack:** Rust (`rust_decimal`, `serde`), PyO3/maturin, UniFFI/Swift, pytest, XCTest.

**Plan file:** `docs/log/p7-plan.md`, committed on `p7.0-readiness` in Task 1.

**Spec:** `docs/log/p7-handover.md` (Task 1 copies the revised `~/Downloads/CheapWings_P7_Explore_Anywhere_Handover.md` there).

## Global Constraints

- Never merge automatically. Each checkpoint is an owner-reviewed PR; follow current branch/PR conventions.
- No live provider probes, new toolchains, paid accounts or changed provider rates without owner approval.
- Discover never claims global coverage. Copy: "Lowest fares found among X discovered destinations; Y checked", never "cheapest anywhere in the world".
- No random destinations, no popularity rank, and no fallback list when discovery fails.
- `plan_search` and the normal Search behaviour stay byte-for-byte unchanged.
- No networking in Rust. No scheduler in Rust. No OctoTrip/swoop on iPad.
- Money crosses boundaries as decimal text plus currency; never floats.
- 120 is the route/date ceiling, not a throughput target.
- A discovery observation is never a checked or verified price.
- Prices in fixtures and examples are fictitious and marked so.
- Every Phase B commit that touches `core/` runs `sh core/update-expected-revision.sh` and commits `backend/src/cheapwings/_core_revision.py` + `apps/ios/CheapWingsCore/Sources/CheapWingsCore/ExpectedCoreRevision.swift`; CI fails otherwise.
- Order (owner, 2026-11-21): iPad/UniFFI before Python/PyO3, and Phase B starts only after Phase A completes.
- Execution: Native (owner, 2026-11-21); stop at every owner gate.
- After code changes: `graphify update .`. Each checkpoint owns `docs/log/p7.x.md`; `WORK_LOG.md` gets a compact entry.

## Review Focus

1. Provider codes with stray case/whitespace (`" cgk"`, `"dps"`) → normalized exactly like Search, not rejected. Pinned in Task 5 `normalizes_codes_like_search`.
2. An observation currency the money table doesn't know (`"XAF"`) and no FX rate → counted as `no_fx`, no panic, other rows unaffected. Pinned in Task 5 `unknown_currency_is_no_fx`.
3. An absurd amount (`"1e40"`, 40 digits) → counted `invalid`, no overflow panic. Pinned in Task 5 `huge_amount_is_invalid`.
4. Zero observations (provider up, nothing priced) → an empty plan with all counts 0 and no error, so the UI can say "no prices" and not "source unavailable". Pinned in Task 5 `empty_input_is_empty_plan`.
5. Dates exactly on `date_from` and `date_through` → included (inclusive window, same as `plan_search`). Pinned in Task 5 `window_is_inclusive`.

---

## Phase A — P7.0 / P7.1 (docs and probe; no product code)

**Branch:** `p7.0-readiness` from current `origin/main`. P5.7 cp3 merged as PR #22 (2026-11-19); P6 as PR #23.

### Task 1: P7.0 readiness record and docs scope delta

**Files:**
- Create: `docs/log/p7-handover.md` (verbatim copy of the revised handover)
- Create: `docs/log/p7.0.md`
- Modify: `docs/02_SYSTEM_ARCHITECTURE.md` (§ "Proposed: destination discovery layer", ~L152–220)
- Modify: `docs/06_IMPLEMENTATION_CHECKPOINTS.md` (P7 section)
- Modify: `WORK_LOG.md`

**Interfaces:** Produces the reuse map later tasks cite. No code.

- [ ] **Step 1:** Copy the spec: `cp ~/Downloads/CheapWings_P7_Explore_Anywhere_Handover.md docs/log/p7-handover.md`.
- [ ] **Step 2:** Write `docs/log/p7.0.md` with these sections:
  - **State:** `git rev-parse origin/main` output; P6 accepted (PR #23); P5.7 cp3 status (merged or not, with PR link).
  - **Reuse map:**
    - `planning::normalize` / `parse_date` (`core/cheapwings-core/src/planning.rs`)
    - `money::fx_convert`
    - `ranking::RankOffer.hidden_city` values (`ThreeValued`, `backend/src/cheapwings/domain/offer.py`)
    - JSON-binding pattern (`skiplagged_parse` in `core/cheapwings-py/src/lib.rs`)
    - `PlanSearchError` pattern (`core/cheapwings-ffi/src/lib.rs`)
    - fixture tests (`core/cheapwings-core/tests/fixtures.rs`, `backend/tests/unit/test_core_fixtures.py`, `apps/ios/CheapWingsCore/Tests/CheapWingsCoreTests/FixtureTests.swift`)
    - revision check (`core/update-expected-revision.sh`)
  - **Future hook points (P7.4, not this plan):** web `backend/src/cheapwings/application/job_runner.py` + `SearchJob`/`WorkItem` (`storage/models.py`), adding a `kind` column; iPad `SearchSession`/`PacedRunner` in `apps/ios/CheapWingsKit`.
- [ ] **Step 3:** Edit `docs/02`:
  - Replace "feeding the existing `plan_search` cap" (~L200) with "`select_discovery_plan` produces an explicit route/date list; `plan_search` is Search-only".
  - Delete the "shared seeded helper in Rust" clause (~L203). Surprise Me is deferred.
- [ ] **Step 4:** In `docs/06` P7, list the checkpoints P7.0–P7.7 as in handover §8. Mark P7.0 in progress.
- [ ] **Step 5:** Verify: `grep -n "plan_search cap\|seeded helper" docs/02_SYSTEM_ARCHITECTURE.md` should print nothing.
- [ ] **Step 6:** Commit, including this plan file `docs/log/p7-plan.md`: `docs(p7.0): readiness record and Discover scope delta`. Open the PR. **Gate: owner approves P7 start.**

### Task 2: P7.1 desk feasibility matrix

**Files:**
- Create: `docs/log/p7.1.md`
- Modify: `docs/03_PROVIDERS_AGGREGATION_PRICING.md` (discovery-candidates subsection: link to p7.1)

**Interfaces:** Produces the probe request the owner approves in Task 3.

- [ ] **Step 1:** In `docs/log/p7.1.md`, build a matrix from **published docs only** (no calls).
  - Rows: Skiplagged Anywhere, Fli/Google Explore, Travelpayouts Data API, swoop/Viajante (reference only).
  - Columns, from handover §4: priced? exact dates? one-way? currency and age? auth/secret on iPad? native `URLSession` reachable? terms on reuse/combining? Indonesian coverage (unknown until probed)?
  - Each cell is "verified (source link)" or "unknown".
- [ ] **Step 2:** Write the probe request.
  - Origins: CGK, SUB, DPS. Windows: two (e.g. +3–5 weeks and +8–10 weeks).
  - Cap: **≤ 1 discovery call per origin per window for Skiplagged = 6 calls total**, plus one `tools/list`. Also say whether Fli Explore is probed.
  - Metrics to record (handover §4 list).
- [ ] **Step 3:** Commit: `docs(p7.1): discovery provider desk matrix and probe request`. **Gate: owner approves the probe budget** (memory: sequence live probes; never run unapproved).

### Task 3: P7.1 approved probe and go/no-go

**Files:**
- Modify: `scripts/provider_probe_skiplagged.py` (add an anywhere mode; reuse its MCP connect, redaction and fixture writing)
- Create (by running): `contracts/fixtures/provider/skiplagged_anywhere_probe_<timestamp>.json`
- Modify: `docs/log/p7.1.md`

**Interfaces:**
- Produces: a verified observation schema. Task 4 maps it into `DiscoveryObservation`, recording which provider field maps to each Rust field.

- [ ] **Step 1:** Add `--anywhere --tool NAME --origin IATA --from YYYY-MM-DD --to YYYY-MM-DD`.
  - It performs exactly one `tools/call`.
  - `--tool` is required: the real callable name comes from `tools/list` output, never a hard-coded guess.
  - It refuses to run without `--i-have-owner-approval`.
- [ ] **Step 2:** Run `python scripts/provider_probe_skiplagged.py` (`tools/list` only). Record the real tool name and argument schema in p7.1.
- [ ] **Step 3:** Run the approved calls one at a time, ≥ 60 s apart. Stop on any 429/401/403 and record it.
- [ ] **Step 4:** For each response, record in p7.1:
  - priced row count, unique destinations, exact dates (yes/no), one-way semantics
  - currency, observation age, hidden-city flag presence, latency, response size
- [ ] **Step 5:** Write the **go/no-go** with the evidence and the proposed field mapping to `DiscoveryObservation` (Task 4).
  - Go requires priced rows **with exact departure dates** for at least two of the three origins.
  - Priced but undated rows are a no-go for Phase B as written. Revise Task 4/5 first, because undated rows are excluded.
  - On no-go, stop this plan here and ask the owner to pick an alternative.
- [ ] **Step 6:** Commit: `docs(p7.1): approved discovery probe results and go/no-go`. **Gate: owner signs go.**

---

## Phase B — P7.2 / P7.3 (shared Rust core)

**Branch:** `p7.2-discovery-core` from `origin/main` after the P7.1 go. All of Phase B is provider-neutral: the mapping from Task 3 lives in the future adapters, not here.

### Task 4: Discovery contract types and shared fixture

**Files:**
- Create: `core/cheapwings-core/src/discovery.rs` (types only in this task)
- Modify: `core/cheapwings-core/src/lib.rs` (add `pub mod discovery;`)
- Modify: `core/cheapwings-core/src/planning.rs` (make `normalize` and `parse_date` `pub(crate)`; no behaviour change)
- Create: `contracts/fixtures/core/discovery_fixtures.json`
- Create: `core/cheapwings-core/tests/discovery.rs`
- Modify: `docs/02_SYSTEM_ARCHITECTURE.md` (contract table: link the fixture as the source of truth)

**Interfaces — Produces (all `#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]`):**

```rust
pub struct DiscoveryObservation {
    pub origin: String,
    pub destination: String,
    pub departure_date: Option<String>,   // YYYY-MM-DD
    pub amount: String,                   // decimal text, as provided
    pub currency: String,
    pub source_id: String,
    pub observed_at: Option<String>,
    pub fetched_at: String,
    pub price_kind: String,               // historical | cached | indicative | unknown
    pub hidden_city: String,              // yes | no | unknown (ThreeValued values)
    pub source_reference: Option<String>,
}
pub struct FxRate { pub currency: String, pub rate: String }   // 1 currency = rate display_currency
pub struct DiscoveryQuery {
    pub origins: Vec<String>,
    pub date_from: String,
    pub date_through: String,
    pub display_currency: String,
    pub budget: Option<String>,           // in display_currency
    pub include_hidden_city: bool,        // same meaning and default (false) as Search's SearchRequest flag
}
// Flat on purpose: serializes as {origin,destination,date,observation_index,comparable_amount},
// exactly the fixture's expect.selected shape (no nested "route").
pub struct SelectedLead {
    pub origin: String, pub destination: String, pub date: String,
    pub observation_index: u32, pub comparable_amount: String,
}
pub struct DiscoveryCounts {
    pub observed: u32, pub selected: u32, pub invalid: u32, pub hidden_city: u32, pub out_of_window: u32,
    pub undated: u32, pub no_fx: u32, pub over_budget: u32, pub superseded: u32, pub capped: u32,
}
pub struct DiscoveryPlan { pub selected: Vec<SelectedLead>, pub counts: DiscoveryCounts }
pub enum DiscoveryError { Plan(PlanError), InvalidCurrency(String), InvalidBudget(String) }
// DiscoveryError::code(): delegates to PlanError::code() | "invalid_currency" | "invalid_budget"
```

`RouteDate` is unchanged. The handover's `fare_restriction` is named `hidden_city` to match `RankOffer`/`SourceOffer`. Unpriced rows never reach Rust; the runtime counts them (P7.4).

- [ ] **Step 1: Write `contracts/fixtures/core/discovery_fixtures.json`** with `"_note": "All prices fictitious."` and the cases below. Every case has `query`, `fx`, `max_route_dates`, `observations`, and `expect` (either `{selected:[{origin,destination,date,observation_index,comparable_amount}], counts:{…}}` or `{error: code}`).

  - **`main`**: query origins `["CGK"]`, `2027-03-01`..`2027-03-07`, display `IDR`, budget `"1500000"`, `include_hidden_city` false (all observations `hidden_city: "no"`); fx `[{"currency":"USD","rate":"16000"}]`; `max_route_dates` 120. Observations, by index:
    - 0: CGK-DPS 03-02, 900000 IDR
    - 1: CGK-DPS 03-03, 850000 IDR
    - 2: CGK-SIN 03-04, 60 USD
    - 3: CGK-KUL 03-05, 50 EUR
    - 4: CGK-BKK, no date, 700000 IDR
    - 5: CGK-HND 03-09, 400000 IDR
    - 6: CGK-CGK 03-02, 100000 IDR
    - 7: CGK-SYD 03-02, 1600000 IDR
    - 8: CGK-LAX 03-02, 2000000 IDR
    - 9: CGK-DPS 03-03, 850000 IDR (other source_id)
    - 10: CGK-SIN 03-04, `"-5"` USD
  - **`main` expect selected:** DPS 03-03 idx 1 `"850000"`; SIN 03-04 idx 2 `"960000"`; SYD 03-02 idx 7 `"1600000"`.
  - **`main` expect counts:** observed 11, selected 3, invalid 2, hidden_city 0, out_of_window 1, undated 1, no_fx 1, over_budget 1, superseded 2, capped 0.
  - **`hidden_city`**: three CGK-DPS/SIN/SYD rows in the window with `hidden_city` `"yes"`, `"unknown"`, `"no"`.
    - `include_hidden_city` false: the `"yes"` row counts `hidden_city` 1; `"unknown"` and `"no"` are selected (Search also admits `unknown`).
    - `include_hidden_city` true: all three are selected.
  - **`capped`**: same as `main` with `max_route_dates` 2. Selected DPS, SIN; capped 1; selected 2.
  - **`tie`**: two destinations at equal comparable price come out in destination-code ascending order.
  - **Errors:** origins `[]` → `no_airports`; reversed dates → `dates_reversed`; display `"XXX"` → `invalid_currency`; budget `"abc"` → `invalid_budget`.
  - **Review Focus cases** (Task 5 names): `normalizes_codes_like_search`, `unknown_currency_is_no_fx`, `huge_amount_is_invalid`, `empty_input_is_empty_plan`, `window_is_inclusive`.
- [ ] **Step 2: Write test `fixture_parses`** in `tests/discovery.rs`. It deserializes every case into the core types and asserts each `expect` counts total equals `observed` (`selected+invalid+hidden_city+out_of_window+undated+no_fx+over_budget+superseded+capped == observed`).
- [ ] **Step 3:** Run `cargo test --manifest-path core/Cargo.toml -p cheapwings-core --test discovery`. Expect FAIL (module missing).
- [ ] **Step 4:** Add the types above, `pub mod discovery;` and the `pub(crate)` visibility changes.
- [ ] **Step 5:** Run the same command. Expect PASS. Then run `cargo test --manifest-path core/Cargo.toml --workspace`: all existing tests still pass (Search unchanged).
- [ ] **Step 6:** Run `sh core/update-expected-revision.sh`, then commit: `feat(p7.2): discovery contract types and shared fixture`. Open the PR. **Gate: owner schema review.** The PR description must ask the owner to confirm two values the spec doesn't pin, both baked into the fixture:
  - `BUDGET_HEADROOM = 1.10`: discovery shortlists leads up to 10% over budget.
  - Undated observations are excluded, not expanded across the window.

### Task 5: `select_discovery_plan`

**Files:**
- Modify: `core/cheapwings-core/src/discovery.rs`
- Modify: `core/cheapwings-core/tests/discovery.rs`

**Interfaces:**
- Consumes: Task 4 types; `planning::{normalize, parse_date}`; `money::fx_convert`.
- Produces: `pub fn select_discovery_plan(observations: &[DiscoveryObservation], query: &DiscoveryQuery, fx: &[FxRate], max_route_dates: u32) -> Result<DiscoveryPlan, DiscoveryError>`.

  The caller computes `max_route_dates = min(120, work_item_limit / enabled_detailed_providers)` (P7.4). Rust doesn't know providers.

- [ ] **Step 1: Write test `fixture_cases`.** For each fixture case, call `select_discovery_plan` and assert equality with `expect` (selected list in order, all counts) or with the error `code()`. The Review Focus cases are fixture entries, each also asserted by name in a `#[test]` of that name for readable failures.
- [ ] **Step 2:** Run `cargo test … --test discovery`. Expect FAIL (function missing).
- [ ] **Step 3: Implement.** Validate the query first:
  - `origins` and dates through `normalize`/`parse_date` (errors wrap as `DiscoveryError::Plan`; reversed → `PlanError::DatesReversed`).
  - `display_currency` through `fx_convert("0", "1", display)` → `InvalidCurrency`.
  - `budget` parsed as a `Decimal` → `InvalidBudget`.

  Then classify each observation in this order, first match wins:
  1. Bad or same airports, origin ∉ query origins, unparseable date, amount not a positive finite decimal (parse failure, overflow, ≤ 0) → `invalid`.
  2. `hidden_city == "yes"` and not `include_hidden_city` → `hidden_city`.
  3. No date → `undated`.
  4. Outside the inclusive window → `out_of_window`.
  5. Comparable = `fx_convert(amount, "1", display)` when currency == display, else `fx_convert(amount, rate, display)` using the matching `FxRate`. A missing rate or an fx error → `no_fx`.
  6. Comparable > `budget × 1.10` → `over_budget`.

  `BUDGET_HEADROOM = 1.10` is a named const with comment: `// discovery may shortlist near-budget leads; only detailed fares are "checked within budget"`.

  Survivors: keep one per destination. The winner is the lowest comparable, ties broken by earlier date, then origin ascending, then lower index. Losers count as `superseded`. Sort winners by comparable ascending, then destination ascending. Take `max_route_dates`; the rest count as `capped`.

  Compare amounts as `Decimal`; `comparable_amount` is `fx_convert`'s text unchanged.
- [ ] **Step 4:** Run `cargo test --manifest-path core/Cargo.toml --workspace`. Expect PASS, including the existing planning fixtures.
- [ ] **Step 5:** Run `sh core/update-expected-revision.sh`, then commit: `feat(p7.3): deterministic discovery shortlist in Rust core`.

### Task 6: UniFFI binding and Swift parity test (iPad first)

**Files:**
- Modify: `core/cheapwings-ffi/src/lib.rs`
- Create: `apps/ios/CheapWingsCore/Tests/CheapWingsCoreTests/DiscoveryFixtureTests.swift`
- Modify (regenerated): the two revision files (Global Constraints)

**Interfaces:**
- Consumes: Task 5 function.
- Produces Swift (UniFFI-generated):
  - `selectDiscoveryPlan(observations: [DiscoveryObservation], query: DiscoveryQuery, fx: [FxRate], maxRouteDates: UInt32) throws -> DiscoveryPlan`
  - Records mirror Task 4 field-for-field (flat `SelectedLead`).
  - Error: `DiscoveryPlanError.Rejected { code, detail }`, the same shape as `PlanSearchError`.

- [ ] **Step 1: Write the tests** in `DiscoveryFixtureTests.swift`. Load `contracts/fixtures/core/discovery_fixtures.json` with the same path logic as `FixtureTests.fixtures`. For each case:
  - assert `selected` (flat `SelectedLead`: origin, destination, date, observationIndex, comparableAmount) and every count, including `hiddenCity`, equal `expect`;
  - for error cases, assert the thrown `Rejected.code` equals `expect.error`.
- [ ] **Step 2:** Run `xcrun swift test --package-path apps/ios/CheapWingsCore`. Expect FAIL (symbol missing).
- [ ] **Step 3:** Add the records, conversion `From` impls and the `#[uniffi::export] fn select_discovery_plan`, following the `plan_search` wrapper (thin delegate; error mapped via `code()` and `to_string()`).
- [ ] **Step 4:** Run `sh core/build-ios.sh && xcrun swift test --package-path apps/ios/CheapWingsCore && xcrun swift test --package-path apps/ios/CheapWingsKit`. Expect PASS.
- [ ] **Step 5:** Run `sh core/update-expected-revision.sh`, then `cargo test --locked --manifest-path core/Cargo.toml --workspace`. Expect PASS.
- [ ] **Step 6:** Commit: `feat(p7.3): discovery shortlist on iPad via UniFFI`.

### Task 7: PyO3 binding, Python parity test, checkpoint log

**Files:**
- Modify: `core/cheapwings-py/src/lib.rs`
- Create: `backend/tests/unit/test_p7_discovery.py`
- Modify (regenerated): the two revision files
- Create: `docs/log/p7.3.md` · Modify: `WORK_LOG.md`, `docs/06_IMPLEMENTATION_CHECKPOINTS.md`

**Interfaces:**
- Consumes: Task 5 function.
- Produces: Python `cheapwings_core.select_discovery_plan(payload: str) -> str`.
  - Input JSON: `{"observations":[…],"query":{…},"fx":[…],"max_route_dates":N}`, the same shape as a fixture case minus `expect`.
  - Output JSON: `DiscoveryPlan`.
  - A `DiscoveryError` raises `ValueError` with message `"{code}: {detail}"`; bad JSON raises `ValueError`.

- [ ] **Step 1: Write the tests** in `test_p7_discovery.py`.
  - `test_binding_exists`: `hasattr(core, "select_discovery_plan")`.
  - `test_fixture_case[<name>]`, parametrized over `contracts/fixtures/core/discovery_fixtures.json`:
    - For normal cases, assert `json.loads(core.select_discovery_plan(json.dumps(case_input))) == case["expect"]`.
    - For error cases, `pytest.raises(ValueError, match=f"^{code}:")`.
  - `test_plan_search_unchanged`: `core.plan_search(["CGK"],["DPS"],"2027-03-01","2027-03-02",120)` returns 2 combos, as before.
- [ ] **Step 2:** Run `.venv/bin/python -m pytest backend/tests/unit/test_p7_discovery.py -q`. Expect FAIL.
- [ ] **Step 3:** Add `#[pyfunction] fn select_discovery_plan(payload: &str) -> PyResult<String>` following `skiplagged_parse`'s serde-JSON pattern, and register it with `wrap_pyfunction!`.
- [ ] **Step 4:** Run `maturin develop --release --locked -m core/cheapwings-py/Cargo.toml`, then `.venv/bin/python -m pytest backend/tests -ra`. Expect all PASS.
- [ ] **Step 5:** Run `sh core/update-expected-revision.sh`.
- [ ] **Step 6:** Write `docs/log/p7.3.md` with:
  - the commands and results from Tasks 4–7;
  - "same fixture, identical output through Rust/UniFFI/PyO3";
  - limitations: no runtime, storage or UI yet; the headroom and undated decisions as confirmed at the Task 4 gate.

  Add a compact `WORK_LOG.md` entry and run `graphify update .`.
- [ ] **Step 7:** Run the full CI-equivalent:

  ```bash
  cargo test --locked --manifest-path core/Cargo.toml --workspace
  .venv/bin/python -m pytest backend/tests -ra
  sh core/build-ios.sh
  xcrun swift test --package-path apps/ios/CheapWingsCore
  xcrun swift test --package-path apps/ios/CheapWingsKit
  ```

  Expect all PASS.
- [ ] **Step 8:** Commit: `feat(p7.3): expose discovery shortlist to Python`. Open the PR. **Gate: owner review of P7.2/P7.3; next is a separate P7.4 runtime plan.**

---

## Out of this plan (next plans, after P7.1 go)

- **P7.4:** web `kind` column + observations table + the single snapshot/plan/enqueue transaction; iPad `SearchSession` stage; the discovery adapter using the Task 3 mapping; computing `max_route_dates`.
- **P7.5/P7.6:** the UIs.
- **P7.7:** acceptance.
- Surprise Me stays deferred.
- `max_stops` (spec §5) is not a discovery filter: observations rarely carry stops. It's applied by detailed search in P7.4.
- The count of unpriced rows dropped at the adapter is a runtime count (P7.4); it never reaches Rust.
