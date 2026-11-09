import type { Job } from "../api/types";

/** Distinguishes "all providers failed" from "no eligible fares" from a transport-level error. */
export function JobErrorPanel({ job, transportError }: { job: Job | null; transportError: Error | null }) {
  if (transportError) {
    return (
      <div className="job-error" role="alert">
        <strong>Could not reach the search service.</strong>
        <p>{transportError.message}</p>
      </div>
    );
  }
  if (!job) return null;

  if (job.status === "failed") {
    return (
      <div className="job-error" role="alert">
        <strong>All providers failed for this search.</strong>
        <p>This is not the same as "no flights found" - the search could not complete.</p>
        {job.warnings.map((w) => (
          <p key={w}>{w}</p>
        ))}
      </div>
    );
  }
  if (job.status === "partial") {
    return (
      <div className="job-warning" role="status">
        <strong>Partial results.</strong>
        <p>Some provider/date combinations failed or were skipped; the cheapest-found result is provisional.</p>
      </div>
    );
  }
  if (job.status === "cancelled") {
    return (
      <div className="job-warning" role="status">
        <strong>Search cancelled.</strong>
        <p>Already-discovered offers are preserved below; this search is explicitly incomplete.</p>
      </div>
    );
  }
  return null;
}
