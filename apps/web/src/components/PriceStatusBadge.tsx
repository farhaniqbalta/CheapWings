import type { PriceStatus } from "../api/types";

const LABELS: Record<PriceStatus, string> = {
  repriced_exact: "Repriced exact",
  recent_search: "Recent search",
  indicative: "Indicative",
  changed_or_unavailable: "Changed / unavailable",
};

const CLASS: Record<PriceStatus, string> = {
  repriced_exact: "badge badge-good",
  recent_search: "badge badge-ok",
  indicative: "badge badge-caution",
  changed_or_unavailable: "badge badge-bad",
};

export function PriceStatusBadge({ status, isEstimate }: { status: PriceStatus; isEstimate: boolean }) {
  return (
    <span className={CLASS[status]}>
      {LABELS[status]}
      {isEstimate && status !== "changed_or_unavailable" ? " (estimate)" : ""}
    </span>
  );
}
