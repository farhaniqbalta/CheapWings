import type { DiscoverJob, DiscoveryOutcome, JobStatus } from "../api/types";

/** Same cap as the shared Rust core's `MAX_DISCOVERY_CALLS` (owner-approved). */
export const MAX_DISCOVERY_CALLS = 31;

function dayNumber(ymd: string): number | null {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(ymd)) return null;
  const ms = Date.parse(`${ymd}T00:00:00Z`);
  return Number.isFinite(ms) ? Math.round(ms / 86_400_000) : null;
}

/** Origins × inclusive days; 0 when the form is incomplete or the range is reversed. */
export function discoveryCallCount(origins: string[], from: string, through: string): number {
  const a = dayNumber(from), b = dayNumber(through);
  if (a === null || b === null || b < a || origins.length === 0) return 0;
  return origins.length * (b - a + 1);
}

/** Plain-language outcome for a finished discovery; null while planned or still running. */
export function outcomeMessage(outcome: DiscoveryOutcome | null, status: JobStatus): string | null {
  switch (outcome) {
    case "unavailable": return "The destination source could not be reached, so no destinations were found. This is not the same as no flights.";
    case "no_prices": return "The destination source answered but returned no usable prices for these dates.";
    case "none_under_budget": return "Destinations were found, but none were under your budget.";
    case "timed_out": return "The search hit its time limit while finding destinations; leads found so far were not checked.";
    default: return status === "failed" ? "Discover could not finish." : null;
  }
}

const DECIMAL = /^\d+(\.\d+)?$/;

/** Compares non-negative decimal strings exactly (no float round-trip); malformed text sorts last. */
export function compareDecimal(a: string, b: string): number {
  const okA = DECIMAL.test(a), okB = DECIMAL.test(b);
  if (!okA || !okB) return okA === okB ? 0 : okA ? -1 : 1;
  const [ai, af = ""] = a.split("."), [bi, bf = ""] = b.split(".");
  const width = Math.max(af.length, bf.length);
  const x = BigInt(ai + af.padEnd(width, "0")), y = BigInt(bi + bf.padEnd(width, "0"));
  return x < y ? -1 : x > y ? 1 : 0;
}

export interface DiscoverRow {
  origin: string;
  destination: string;
  date: string;
  leadAmount: string;               // provisional discovery price
  checkedAmount: string | null;     // cheapest checked comparable fare for this route and date
  checkedItineraryId: string | null;
  state: "checked" | "checking" | "no_fare" | "check_failed";
}

/** One row per shortlisted destination; checked fares first (by checked price), then leads.
 *  The checked fare is the server's cheapest stored quote for that route/date (all pages). */
export function discoverRows(job: DiscoverJob): DiscoverRow[] {
  const finished = ["completed", "partial", "failed", "cancelled"].includes(job.status);
  const rows = job.discovery.shortlist.map((lead): DiscoverRow => ({
    origin: lead.origin, destination: lead.destination, date: lead.date, leadAmount: lead.comparable_amount,
    checkedAmount: lead.checked_amount ?? null, checkedItineraryId: lead.checked_itinerary_id ?? null,
    state: lead.checked_amount ? "checked" : lead.check_status === "failed" ? "check_failed" : finished ? "no_fare" : "checking",
  }));
  const checked = rows.filter(r => r.checkedAmount).sort((x, y) => compareDecimal(x.checkedAmount!, y.checkedAmount!));
  const rest = rows.filter(r => !r.checkedAmount).sort((x, y) => compareDecimal(x.leadAmount, y.leadAmount));
  return [...checked, ...rest];
}
