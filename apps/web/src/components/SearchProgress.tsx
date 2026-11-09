import type { Job } from "../api/types";

const STATUS_LABEL: Record<Job["status"], string> = {
  queued: "Queued",
  running: "Searching",
  completed: "Complete",
  partial: "Partial",
  failed: "Failed",
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
  const active = job.status === "queued" || job.status === "running";
  return (
    <section className="search-progress" aria-live="polite">
      <div className="progress-headline">
        <span className={`status-pill status-${job.status}`}>{STATUS_LABEL[job.status]}</span>
        {active && <span className="phase-label">{job.phase}</span>}
        <span>
          Coverage: {job.covered_route_date_combinations} / {job.total_route_date_combinations} route-date pairs
        </span>
        {active && (
          <button type="button" onClick={onCancel} disabled={cancelling} className="cancel-button">
            {cancelling ? "Cancelling..." : "Cancel search"}
          </button>
        )}
      </div>

      <ul className="provider-coverage">
        {job.provider_status.map((p) => (
          <li key={p.provider_id}>
            <strong>{p.provider_id}</strong>: {p.succeeded} succeeded
            {p.failed > 0 ? `, ${p.failed} failed` : ""}
            {p.cancelled > 0 ? `, ${p.cancelled} cancelled` : ""}
            {p.skipped_unsupported > 0 ? `, ${p.skipped_unsupported} skipped` : ""}
            {p.disabled_reason ? ` (disabled: ${p.disabled_reason})` : ""}
          </li>
        ))}
      </ul>

      <p className="inventory-note">
        Inventory completeness: unknown. {job.exact_reprice_attempted > 0 && (
          <>Reprice: {job.exact_reprice_succeeded}/{job.exact_reprice_attempted} checked.</>
        )}
      </p>

      {job.warnings.length > 0 && (
        <ul className="job-warnings">
          {job.warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
