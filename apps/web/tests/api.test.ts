import test from "node:test";
import assert from "node:assert/strict";
import { errorMessage } from "../src/api/errors.ts";
import { getOwnerToken, setOwnerToken } from "../src/api/session.ts";

test("FastAPI string, field-array and non-JSON errors remain actionable", () => {
  assert.equal(errorMessage({ detail: "Owner bearer token required" }, "401"), "Owner bearer token required");
  assert.equal(errorMessage({ detail: "Live fare data expired; start a new search" }, "410"), "Live fare data expired; start a new search");
  assert.equal(errorMessage({ detail: [{ msg: "Bad date" }, { msg: "Bad airport" }] }, "422"), "Bad date; Bad airport");
  for (const detail of [null, "html body", { detail: 1 }, { detail: [{}] }]) {
    assert.equal(errorMessage(detail, "503 Service unavailable"), "503 Service unavailable");
  }
});

test("owner token can be applied and cleared without browser storage", () => {
  assert.equal(getOwnerToken(), "");
  setOwnerToken(" runtime-only-test-token ");
  assert.equal(getOwnerToken(), "runtime-only-test-token");
  setOwnerToken("");
  assert.equal(getOwnerToken(), "");
});


test("flight dates preserve origin-local offsets rather than the browser timezone", async () => {
  const { flightLocalTime } = await import("../src/lib/time.ts");
  assert.equal(flightLocalTime("2026-12-16T07:00:00+11:00"), "2026-12-16 07:00 UTC+11:00");
  assert.equal(flightLocalTime("2026-12-16T10:00:00"), "2026-12-16 10:00 (timezone unknown)");
  assert.equal(flightLocalTime("2026-12-16T07:00:00Z"), "2026-12-16 07:00 UTC");
});
