import type { Job } from "../api/types";

const LABEL: Record<Job["status"], string> = {
  queued: "Queued", running: "Searching", completed: "Search complete",
  partial: "Partially complete", failed: "Search failed", cancelled: "Cancelled",
};

/** Compact real-data status band. Provider work and route/date coverage stay separate. */
export function P46SearchProgress({ job, onCancel, cancelling }: {
  job: Job; onCancel: () => void; cancelling: boolean;
}) {
  const active = job.status === "queued" || job.status === "running";
  const unpriced = job.coverage.filter(item => item.work_type === "detailed")
    .reduce((total, item) => total + item.unpriced_candidate_count, 0);
  const errors = Object.entries(job.coverage.reduce<Record<string, number>>((counts, item) => {
    if (item.work_type === "detailed" && item.error_code) {
      const label = item.error_code === "schema_changed" ? "Unrecognized source response" : item.error_code.replaceAll("_", " ");
      const key = `${item.provider_id}: ${label}`;
      counts[key] = (counts[key] ?? 0) + 1;
    }
    return counts;
  }, {}));
  const phase = job.phase === "verifying" ? "Checking selected prices" :
    job.phase === "searching" ? "Comparing source results" : "Search finalized";
  return (
    <section className="p46-job-strip" aria-label="Search status and source coverage">
      <div className="p46-job-first">
        <div className="p46-job-heading">
          <span className="p46-job-indicator" aria-hidden="true">●</span>
          <span className="p46-job-status">{LABEL[job.status]}</span>
          {active && <span className="p46-job-phase">{phase}</span>}
          {active && <button type="button" onClick={onCancel} disabled={cancelling} className="cancel-button">
            {cancelling ? "Cancelling…" : "Cancel search"}</button>}
        </div>
        <div className="p46-job-query">
          <strong>{job.query.origins.join(", ")} <span aria-hidden="true">→</span> {job.query.destinations.join(", ")}</strong>
          <span>{job.query.departure_date_from} – {job.query.departure_date_through} · One-way · 1 adult · Economy · {job.query.display_currency ?? "IDR"}</span>
        </div>
        <div className="p46-job-counts">
          <span>ROUTE/DATE <b>{job.covered_route_date_combinations}/{job.total_route_date_combinations}</b></span>
          <span>PROVIDER WORK <b>{job.succeeded_provider_work_items}/{job.total_provider_work_items}</b></span>
        </div>
      </div>
      <div className="p46-job-foot">
        {job.query.include_hidden_city && <span className="p46-job-caution">Hidden-city inclusion requested; risk is not presumed safe.</span>}
        {job.coverage.some(item => item.result_origin === "cache" || item.result_origin === "shared_inflight") && <span>
          Provider work: {job.coverage.filter(item => item.work_type === "detailed" && item.status.startsWith("succeeded") && item.result_origin === "cache").length} cached · {job.coverage.filter(item => item.work_type === "detailed" && item.status.startsWith("succeeded") && item.result_origin === "shared_inflight").length} shared · {job.coverage.filter(item => item.work_type === "detailed" && item.status.startsWith("succeeded") && (!item.result_origin || item.result_origin === "live")).length} newly searched.
        </span>}
        <span><b>Inventory completeness: unknown.</b></span>
        {job.failed_provider_work_items > 0 && <span className="p46-job-caution">{job.failed_provider_work_items} source work failed</span>}
        {unpriced > 0 && <span className="p46-job-caution">{unpriced} candidates unpriced</span>}
        <details className="p46-job-details"><summary>Source coverage and caveats</summary>
          <div className="p46-job-detail-body">
            <p>Fare preferences: {job.query.max_stops == null ? "Any stops" : `Up to ${job.query.max_stops} stops`} · {job.query.checked_bags_required ? "Checked bag required" : "Checked bag not required"} · {job.query.include_basic_economy === false ? "Basic economy excluded" : "Basic economy included"}. Dates are inclusive.</p>
            <p>Route/date coverage counts unique pairs with a successful source response. Provider work counts source tasks independently. Neither measures the completeness of flight inventory.</p>
            <p>{job.succeeded_empty} source work items returned no matching fares · {job.failed_provider_work_items} failed · {job.skipped_unsupported} skipped · {job.cancelled_provider_work_items} cancelled.</p>
            {job.status === "queued" || job.status === "running" ? <p>The background worker continues eligible searches while this job is active. Queued work may be waiting for provider pacing or cooldowns.</p> : null}
            {job.exact_reprice_attempted > 0 && <p>Exact reprice successes: {job.exact_reprice_succeeded} / {job.exact_reprice_attempted} attempts.</p>}
            {job.query.include_hidden_city && <p>Hidden-city inclusion requested. Classification depends on individual sources and is not presumed safe.</p>}
            {job.provider_status.length > 0 && <ul>{job.provider_status.map(source => (
              <li key={source.provider_id}><strong>{source.provider_id}</strong>: {source.succeeded} succeeded, {source.pending ?? 0} queued, {source.running ?? 0} running, {source.retry_wait ?? 0} waiting to retry, {source.failed} failed, {source.cancelled} cancelled, {source.skipped_unsupported} skipped
                {source.disabled_reason && ` · disabled: ${source.disabled_reason}`}</li>
            ))}</ul>}
            {errors.length > 0 && <ul>{errors.map(([label, count]) => <li key={label}>{label}: {count} work items</li>)}</ul>}
            {job.warnings.length > 0 && <ul>{job.warnings.map((warning, index) =>
              <li key={`${index}-${warning}`}>{warning.includes("unpriced_candidate_count") ? `${unpriced} source candidates had no price and are excluded from priced results.` : warning}</li>)}</ul>}
          </div>
        </details>
      </div>
      <p className="sr-only" aria-live="polite" aria-atomic="true">{LABEL[job.status]}. {job.covered_route_date_combinations} of {job.total_route_date_combinations} route-date pairs covered.</p>
    </section>
  );
}
