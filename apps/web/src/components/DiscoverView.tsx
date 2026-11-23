import type { DiscoverJob, Results } from "../api/types";
import { discoverRows, outcomeMessage } from "../lib/discover";
import { formatMoney } from "../lib/money";

const LABEL: Record<DiscoverJob["status"], string> = {
  queued: "Queued", running: "Discovering", completed: "Discover complete",
  partial: "Partially complete", failed: "Discover failed", cancelled: "Cancelled",
};

/** P7.5: discovery progress, honest coverage, provisional leads and checked fares per destination. */
export function DiscoverView({ job, results, onCancel, cancelling }: {
  job: DiscoverJob; results: Results | null; onCancel: () => void; cancelling: boolean;
}) {
  const d = job.discovery;
  const currency = job.query.display_currency ?? "IDR";
  const active = job.status === "queued" || job.status === "running";
  const rows = discoverRows(job, results?.itineraries ?? []);
  const message = outcomeMessage(d.outcome, job.status);
  const stage = job.phase === "discovering" ? "Finding destinations" : job.phase === "searching" ? "Checking fares" : "Finished";
  return (
    <section className="p46-job-strip discover-view" aria-label="Discover status and destinations">
      <div className="p46-job-first">
        <div className="p46-job-heading">
          <span className="p46-job-indicator" aria-hidden="true">●</span>
          <span className="p46-job-status">{LABEL[job.status]}</span>
          {active && <span className="p46-job-phase">{stage}</span>}
          {active && <button type="button" onClick={onCancel} disabled={cancelling} className="cancel-button">
            {cancelling ? "Cancelling…" : "Cancel Discover"}</button>}
        </div>
        <div className="p46-job-query">
          <strong>{job.query.origins.join(", ")} <span aria-hidden="true">→</span> anywhere</strong>
          <span>{job.query.departure_date_from} – {job.query.departure_date_through} · One-way · {currency}
            {job.query.budget ? ` · Budget ${formatMoney(job.query.budget, currency)}` : ""}</span>
        </div>
        <div className="p46-job-counts">
          <span>DISCOVERY CALLS <b>{d.calls_done}/{d.calls_planned}</b></span>
          <span>DESTINATIONS FOUND <b>{d.discovered_destinations}</b></span>
          <span>CHECKS <b>{job.succeeded_checks}/{job.total_checks}</b></span>
        </div>
      </div>
      <div className="p46-job-foot">
        {job.warnings.map((w, i) => <span key={i}>{w}</span>)}
        {d.calls_failed > 0 && <span className="p46-job-caution">{d.calls_failed} discovery calls failed</span>}
        {d.unpriced > 0 && <span>{d.unpriced} destinations had no price and were left out</span>}
        {d.stopped_providers.length > 0 && <span className="p46-job-caution">Stopped by the source: {d.stopped_providers.join(", ")}</span>}
      </div>
      {message && <p className="empty-state" role="status">{message}</p>}
      {rows.length > 0 && <ol className="discover-rows" aria-label="Destinations">
        {rows.map(row => <li key={`${row.origin}-${row.destination}-${row.date}`} className={`discover-row discover-${row.state}`}>
          <span className="discover-dest"><b>{row.destination}</b> <small>from {row.origin} · {row.date}</small></span>
          {row.checkedAmount
            ? <span className="discover-checked"><small>Checked fare</small> <b>{formatMoney(row.checkedAmount, currency)}</b></span>
            : <span className="discover-pending"><small>{row.state === "checking" ? "Checking…" : "No checked fare"}</small></span>}
          <span className="discover-lead"><small>Discovery price (provisional)</small> {formatMoney(row.leadAmount, currency)}</span>
        </li>)}
      </ol>}
    </section>
  );
}
