import { ApiError } from "../api/client";
import type { Job } from "../api/types";

/** A transport error never masquerades as a successful search with no flights. */
export function JobErrorPanel({ job, transportError }: { job: Job | null; transportError: Error | null }) {
  if (transportError) {
    const status = transportError instanceof ApiError ? transportError.status : null;
    const heading = status === 401 ? "Private server access required" :
      status === 410 ? "These fare results have expired" :
      status === 429 ? "Search request limit reached" :
      "Could not update this search";
    const guidance = status === 401 ? "Open Private server access above, apply your owner token, then retry." :
      status === 410 ? "Old price evidence is no longer available. Start a new search for fresh offers." :
      status === 429 ? "Too many requests were made. Retry later; existing completed fares are not a new booking guarantee." :
      "Check your connection and retry. A running server job may still be progressing.";
    return (
      <div className="job-error" role="alert">
        <strong>{heading}</strong>
        <p>{guidance}</p>
        <p className="error-technical">{transportError.message}</p>
      </div>
    );
  }
  if (!job) return null;

  if (job.status === "failed") return (
    <div className="job-error" role="alert">
      <strong>The search did not return usable source coverage.</strong>
      <p>Source failure is not evidence that no flights exist. Review provider coverage or start a narrower search.</p>
      {job.warnings.map((warning, index) => <p key={`${index}-${warning}`}>{warning}</p>)}
    </div>
  );
  if (job.status === "partial") return (
    <div className="job-warning" role="status">
      <strong>Partial results — some source work did not finish.</strong>
      <p>Available offers remain visible. Prices cover successful source responses only; coverage is incomplete.</p>
    </div>
  );
  if (job.status === "cancelled") return (
    <div className="job-warning" role="status">
      <strong>Search cancelled.</strong>
      <p>Found offers are retained. These quotes were gathered before cancellation. Unfinished routes and sources remain unsearched.</p>
    </div>
  );
  return null;
}
