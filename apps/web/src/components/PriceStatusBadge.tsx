import type { PriceStatus } from "../api/types";

const LABELS: Record<PriceStatus, string> = {
  repriced_exact: "Repriced exact",
  recent_search: "Recent source search",
  indicative: "Indicative price",
  changed_or_unavailable: "Changed / unavailable",
};

export function PriceStatusBadge({ status, isEstimate }: { status: PriceStatus; isEstimate: boolean }) {
  // A contradictory upstream status must never be presented as an exact checked price.
  const label = status === "repriced_exact" && isEstimate
    ? "Estimate — exact price unconfirmed"
    : `${LABELS[status]}${isEstimate && status !== "changed_or_unavailable" ? " · estimate" : ""}`;
  const className = status === "changed_or_unavailable" ? "badge badge-bad" :
    isEstimate || status === "indicative" ? "badge badge-caution" :
    status === "repriced_exact" ? "badge badge-good" : "badge badge-ok";
  return <span className={className}>{label}</span>;
}
