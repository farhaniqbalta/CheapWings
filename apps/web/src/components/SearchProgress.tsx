import type { Job } from "../api/types";

const STATUS_LABEL: Record<Job["status"], string> = {
  queued: "Queued",
  running: "Searching",
  completed: "Search complete",
  partial: "Partially complete",
  failed: "Search failed",
  cancelled: "Cancelled",
};

export function SearchProgress({
  job,
  onCancel,
  cancelling,
}: {
  job: Job;
  onCancel: () => void;
  cancelling: boolean;
}) {
  const unpriced = job.coverage.filter(item => item.work_type === "detailed")
    .reduce((count, item) => count + item.unpriced_candidate_count, 0);
  const query = job.query;
  const errorSummary = Object.entries(job.coverage.reduce<Record<string, number>>((counts, item) => {
    if (item.work_type === "detailed" && item.error_code) {
      const label = item.error_code === "schema_changed" ? "Unrecognized source response"
        : item.error_code.replaceAll("_", " ");
      const key = `${item.provider_id}: ${label}`;
      counts[key] = (counts[key] ?? 0) + 1;
    }
    return counts;
  }, {}));
  const active = job.status === "queued" || job.status === "running";
  const phaseLabel = job.phase === "verifying" ? "Checking selected prices" :
    job.phase === "searching" ? "Comparing source results" : "Search finalized";

  return (
    <section className="search-progress" aria-labelledby="search-progress-heading">
      <div className="progress-heading-row">
        <div>
          <p className="section-kicker">SEARCH ACTIVITY</p>
          <h2 id="search-progress-heading">Your search</h2>
          <div className="progress-headline">
            <span className={`status-pill status-${job.status}`}>{STATUS_LABEL[job.status]}</span>
            {active && <span className="phase-label">{phaseLabel}</span>}
          </div>
        </div>
        {active && (
          <button type="button" onClick={onCancel} disabled={cancelling} className="cancel-button">
            {cancelling ? "Cancelling…" : "Cancel search"}
          </button>
        )}
      </div>

      <div className="query-summary">
        <strong>{query.origins.join(", ")} → {query.destinations.join(", ")}</strong>
        <span>{query.departure_date_from} through {query.departure_date_through}, inclusive</span>
        <span>One-way · 1 adult · Economy · {query.display_currency ?? "IDR"}
          {query.max_stops == null ? " · Any stops" : ` · Up to ${query.max_stops} stops`}
          {query.checked_bags_required ? " · Checked bag required" : " · Checked bag not required"}
          {query.include_basic_economy === false ? " · Basic economy excluded" : " · Basic economy included"}
        </span>
        {query.include_hidden_city && <small>Hidden-city inclusion requested; available classifications depend on the source.</small>}
      </div>

      <div className="coverage-grid">
        <div className="coverage-stat">
          <span className="coverage-label">Routes × departure days covered</span>
          <strong>{job.covered_route_date_combinations} <span>of {job.total_route_date_combinations}</span></strong>
          <progress
            aria-label="Route-date pairs with at least one successful source response"
            max={Math.max(1, job.total_route_date_combinations)}
            value={job.covered_route_date_combinations}
          />
          <small>Unique route/date combinations; not flight inventory.</small>
        </div>
        <div className="coverage-stat">
          <span className="coverage-label">Provider work succeeded</span>
          <strong>{job.succeeded_provider_work_items} <span>of {job.total_provider_work_items}</span></strong>
          <progress
            aria-label="Successfully completed provider work items"
            max={Math.max(1, job.total_provider_work_items)}
            value={job.succeeded_provider_work_items}
          />
          <small>
            {job.succeeded_empty} returned no matching fares · {job.failed_provider_work_items} failed · {job.skipped_unsupported} skipped
          </small>
        </div>
      </div>

      {job.coverage.some(item => item.result_origin === "cache" || item.result_origin === "shared_inflight") && (
        <p className="inventory-note">
          Provider work: {job.coverage.filter(item => item.work_type === "detailed" && item.status.startsWith("succeeded") && item.result_origin === "cache").length} cached · {job.coverage.filter(item => item.work_type === "detailed" && item.status.startsWith("succeeded") && item.result_origin === "shared_inflight").length} shared · {job.coverage.filter(item => item.work_type === "detailed" && item.status.startsWith("succeeded") && (!item.result_origin || item.result_origin === "live")).length} newly searched. Original observation times are retained.
        </p>
      )}
      {(job.failed_provider_work_items > 0 || unpriced > 0) && (
        <p className="coverage-caution">{job.failed_provider_work_items} source work items failed · {unpriced} candidates had no price</p>
      )}
      <details className="coverage-details">
      <summary>Source coverage and caveats</summary>
      <h3 className="coverage-subhead">Source coverage</h3>
      {job.provider_status.length > 0 ? (
        <ul className="provider-coverage">
          {job.provider_status.map((p) => (
            <li key={p.provider_id}>
              <strong>{p.provider_id}</strong>
              <span>{p.succeeded} succeeded · {p.pending ?? 0} queued · {p.running ?? 0} running · {p.retry_wait ?? 0} waiting to retry · {p.failed} failed · {p.cancelled} cancelled · {p.skipped_unsupported} skipped</span>
              {p.disabled_reason && <small>Unavailable: {p.disabled_reason}</small>}
            </li>
          ))}
        </ul>
      ) : <p className="inventory-note">Provider work has not started yet.</p>}

      {job.status === "queued" || job.status === "running" ? (
        <p className="inventory-note">
          The background worker continues eligible searches while this job is active. Queued work may be waiting for provider pacing or cooldowns.
        </p>
      ) : null}
      {errorSummary.length > 0 && <ul className="source-errors">{errorSummary.map(([label, count]) =>
        <li key={label}>{label}: {count} work items</li>)}</ul>}
      {job.warnings.length > 0 && (
        <ul className="job-warnings">{job.warnings.map((warning, index) =>
          <li key={`${index}-${warning}`}>{warning.includes("unpriced_candidate_count")
            ? `${unpriced} source candidates had no price and are excluded from priced results.`
            : warning}</li>)}</ul>
      )}
      </details>
      <p className="inventory-note">
        <strong>Flight inventory completeness: unknown.</strong>
        {job.exact_reprice_attempted > 0 &&
          ` Exact reprice successes: ${job.exact_reprice_succeeded} across ${job.exact_reprice_attempted} attempts.`}
      </p>
      <p className="sr-only" aria-live="polite" aria-atomic="true">
        {STATUS_LABEL[job.status]}. {job.covered_route_date_combinations} of {job.total_route_date_combinations} route-date pairs covered.
      </p>

    </section>
  );
}
