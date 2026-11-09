import type { PublicOffer } from "../api/types";
import { formatMoney } from "../lib/money";
import { FareRiskNotice } from "./FareRiskNotice";
import { PriceStatusBadge } from "./PriceStatusBadge";

function describeLink(offer: PublicOffer): string | null {
  if (!offer.link || offer.link_scope === "unavailable") return null;
  if (offer.link_scope === "exact_offer") return "Open exact offer";
  if (offer.link_scope === "itinerary") return "Open this itinerary";
  return "Open search (not tied to this exact fare)";
}

export function OfferList({ offers, rankedQuoteId }: { offers: PublicOffer[]; rankedQuoteId: string }) {
  return (
    <ul className="offer-list">
      {offers.map((offer) => {
        const linkLabel = describeLink(offer);
        const amount = offer.comparable_amount ?? offer.amount_original;
        const currency = offer.comparable_currency ?? offer.currency_original;
        return (
          <li
            key={offer.quote_id}
            className={offer.quote_id === rankedQuoteId ? "offer offer-ranked" : "offer"}
          >
            <div className="offer-price-row">
              <span className="offer-price">{formatMoney(amount, currency)}</span>
              <PriceStatusBadge status={offer.price_status} isEstimate={offer.is_estimate} />
            </div>
            <div className="offer-meta">
              {offer.provider_id}
              {offer.seller ? ` - ${offer.seller}` : " - seller unknown"}
              {offer.fare_family ? ` - ${offer.fare_family}` : ""}
              {offer.basic_economy === true ? " - basic economy" : ""}
            </div>
            <div className="offer-meta">
              Checked bag:{" "}
              {offer.checked_bag === "yes" ? "included" : offer.checked_bag === "no" ? "not included" : "unknown"}
              {" - checked "}
              {new Date(offer.retrieved_at).toLocaleString()}
              {offer.repriced_at ? ` - repriced ${new Date(offer.repriced_at).toLocaleString()}` : ""}
            </div>
            <FareRiskNotice offer={offer} />
            {offer.warnings.length > 0 && (
              <ul className="offer-warnings">
                {offer.warnings.map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            )}
            {linkLabel && offer.link ? (
              <a href={offer.link} target="_blank" rel="noopener noreferrer nofollow">
                {linkLabel}
              </a>
            ) : (
              <span className="link-unavailable">Seller link unavailable</span>
            )}
          </li>
        );
      })}
    </ul>
  );
}
