import test from "node:test";
import assert from "node:assert/strict";
import { MAX_DISCOVERY_CALLS, compareDecimal, discoverRows, discoveryCallCount, outcomeMessage } from "../src/lib/discover.ts";
import type { DiscoverJob, PublicItinerary } from "../src/api/types.ts";

test("discovery call count is origins × inclusive days, 0 when invalid", () => {
  assert.equal(MAX_DISCOVERY_CALLS, 31);
  assert.equal(discoveryCallCount(["CGK"], "2027-03-01", "2027-03-07"), 7);
  assert.equal(discoveryCallCount(["CGK", "SUB"], "2027-03-01", "2027-03-16"), 32);
  assert.equal(discoveryCallCount(["CGK"], "2027-03-07", "2027-03-01"), 0);
  assert.equal(discoveryCallCount([], "2027-03-01", "2027-03-07"), 0);
  assert.equal(discoveryCallCount(["CGK"], "2027-02-28", "2027-03-01"), 2);
});

test("every outcome has its own message; unavailable is never 'no destinations'", () => {
  assert.match(outcomeMessage("unavailable", "failed")!, /could not be reached/);
  assert.match(outcomeMessage("no_prices", "completed")!, /no usable prices/);
  assert.match(outcomeMessage("none_under_budget", "completed")!, /budget/);
  assert.match(outcomeMessage("timed_out", "partial")!, /time limit/);
  assert.equal(outcomeMessage("planned", "completed"), null);
  assert.equal(outcomeMessage(null, "running"), null);
});

test("decimal comparison never goes through floats", () => {
  assert.equal(compareDecimal("640000", "800000"), -1);
  assert.equal(compareDecimal("900719925474099312345.10", "900719925474099312345.09"), 1);
  assert.equal(compareDecimal("1.50", "1.5"), 0);
});

const job = (status: DiscoverJob["status"], shortlist: [string, string, string][]): DiscoverJob => ({
  job_id: "d1", provider_ids: ["fli"], status, phase: status === "running" ? "searching" : "done", cancel_requested: false,
  created_at: "2027-02-20T00:00:00Z", updated_at: "2027-02-20T00:00:00Z",
  query: { origins: ["CGK"], departure_date_from: "2027-03-01", departure_date_through: "2027-03-02", display_currency: "IDR", budget: null, max_stops: null },
  discovery: { calls_planned: 2, calls_done: 2, calls_failed: 0, unpriced: 0, discovered_destinations: shortlist.length, counts: null,
               outcome: "planned", stopped_providers: [],
               shortlist: shortlist.map(([destination, date, comparable_amount]) => ({ origin: "CGK", destination, date, comparable_amount })) },
  total_checks: 2, succeeded_checks: 1, failed_checks: 0, checked_route_dates: 1, provider_status: [], warnings: [],
});

const itinerary = (destination: string, date: string, amount: string, id = destination): PublicItinerary => ({
  itinerary_id: id, identity_confidence: "insufficient_identity", origin: "CGK", destination,
  departure_local: `${date}T07:00:00+07:00`, arrival_local: `${date}T10:00:00+08:00`, duration_minutes: 120, stops: 0, segments: [],
  ranked_quote_id: "q", offers: [{ quote_id: "q", provider_id: "fli", seller: null, fare_family: null, cabin: "economy", basic_economy: null,
    amount_original: amount, currency_original: "IDR", comparable_amount: amount, comparable_currency: "IDR", comparison_status: "extra_cost_unknown",
    checked_bag: "unknown", hidden_city: "no", self_transfer: "no", price_status: "indicative", is_estimate: true,
    retrieved_at: "2027-02-20T00:00:00Z", repriced_at: null, link: null, link_scope: "unavailable", warnings: [] }],
});

test("a lead without a checked fare stays provisional", () => {
  const rows = discoverRows(job("running", [["DPS", "2027-03-01", "640000"]]), []);
  assert.deepEqual(rows.map(r => [r.destination, r.leadAmount, r.checkedAmount, r.state]), [["DPS", "640000", null, "checking"]]);
  assert.equal(discoverRows(job("completed", [["DPS", "2027-03-01", "640000"]]), [])[0].state, "no_fare");
});

test("checked fares rank first by checked price; only the lead's date counts", () => {
  const rows = discoverRows(job("completed", [["DPS", "2027-03-01", "640000"], ["SIN", "2027-03-01", "800000"], ["BKK", "2027-03-02", "900000"]]),
    [itinerary("SIN", "2027-03-01", "750000"), itinerary("SIN", "2027-03-01", "990000", "SIN-2"), itinerary("DPS", "2027-03-02", "100")]);
  assert.deepEqual(rows.map(r => [r.destination, r.checkedAmount, r.state]),
    [["SIN", "750000", "checked"], ["DPS", null, "no_fare"], ["BKK", null, "no_fare"]]);
  assert.equal(rows[0].checkedItineraryId, "SIN");
});
