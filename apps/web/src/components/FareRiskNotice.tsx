import type { PublicOffer } from "../api/types";

/** Text labels always accompany color; never color-only risk signaling. */
export function FareRiskNotice({ offer }: { offer: PublicOffer }) {
  const notices: string[] = [];
  if (offer.hidden_city === "yes") notices.push("Hidden-city fare: enforcement risk, not a protected connection.");
  if (offer.hidden_city === "unknown") notices.push("Hidden-city risk unknown for this fare.");
  if (offer.self_transfer === "yes") notices.push("Self-transfer: you must recheck in, no protection if a leg is delayed.");
  if (offer.self_transfer === "unknown") notices.push("Self-transfer risk unknown.");
  if (offer.checked_bag === "unknown") notices.push("Checked-bag cost unknown; may not be the full payable total.");
  if (offer.comparison_status === "missing_required_baggage")
    notices.push("Required checked bag not confirmed included; price is not a verified total.");
  if (offer.comparison_status === "currency_unresolved")
    notices.push("Could not confirm a comparable amount in your selected currency.");
  if (notices.length === 0) return null;
  return (
    <ul className="fare-risk-notice">
      {notices.map((n) => (
        <li key={n}>{n}</li>
      ))}
    </ul>
  );
}
