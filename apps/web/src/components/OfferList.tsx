import type { PublicOffer } from "../api/types";
import { formatMoney } from "../lib/money";
import { FareRiskNotice } from "./FareRiskNotice";
import { PriceStatusBadge } from "./PriceStatusBadge";

function describeLink(offer: PublicOffer): string | null {
  if (!offer.link || offer.link_scope === "unavailable") return null;
  if (offer.link_scope === "exact_offer") return "Open exact offer";
  if (offer.link_scope === "itinerary") return "Open itinerary page";
  return "Open source search";
}

const BAG_LABEL = { yes: "Included", no: "Not included", unknown: "Unknown" } as const;
const RISK_LABEL = { yes: "Yes", no: "No", unknown: "Unknown" } as const;

const COMPARISON_LABEL = {
  eligible_total_known: "Comparable under selected fare filters",
  extra_cost_unknown: "Possible extra fees — payable total unknown",
  missing_required_baggage: "Required baggage not confirmed in price",
  ineligible: "Not eligible for checked ranking",
  currency_unresolved: "Comparable currency unresolved",
} as const;

export function OfferList({ offers, rankedQuoteId }: { offers: PublicOffer[]; rankedQuoteId: string }) {
  return (
    <ul className="offer-list">
      {offers.map((offer) => {
        const linkLabel = describeLink(offer);
        const ranked = offer.quote_id === rankedQuoteId;
        const amount = offer.comparable_amount ?? offer.amount_original;
        const currency = offer.comparable_currency ?? offer.currency_original;
        const feeCompleteAndKnownRisk = offer.comparison_status === "eligible_total_known" && offer.hidden_city === "no";
        return (
          <li key={offer.quote_id} className={ranked ? "offer offer-ranked" : "offer"}>
            <div className="offer-main">
              <div className="offer-identification">
                <strong>{offer.seller ?? "Seller not identified"}</strong>
                <span className="offer-provider">via {offer.provider_id}</span>
                {offer.result_origin === "cache" && <span className="offer-provider">
                  Observed {new Date(offer.retrieved_at).toLocaleString()} · Cached observation
                </span>}
                {offer.result_origin === "shared_inflight" && <span className="offer-provider">Shared source observation</span>}
                {ranked && <span className="ranked-indicator">Ranked quote</span>}
              </div>
              <div className="offer-amount">
                <strong className="offer-price">{formatMoney(amount, currency)}</strong>
                <PriceStatusBadge status={offer.price_status} isEstimate={offer.is_estimate} />
              </div>
              <div className="offer-action">
                {linkLabel && offer.link ? (
                  <a href={offer.link} target="_blank" rel="noopener noreferrer nofollow"
                     aria-label={`${linkLabel} from ${offer.seller ?? offer.provider_id} (opens new tab)`}>
                    {linkLabel} <span aria-hidden="true">↗</span>
                  </a>
                ) : <span className="link-unavailable">Seller link unavailable</span>}
                {offer.link_scope === "generic_search" && linkLabel && (
                  <small>Search page, not this confirmed fare</small>
                )}
              </div>
            </div>
            <div className="offer-facts">
              <span><b>Checked bag</b>{BAG_LABEL[offer.checked_bag]}</span>
              <span><b>Fare type</b>{offer.fare_family ?? "Unknown"}</span>
              <span><b>Basic economy</b>{offer.basic_economy == null ? "Unknown" : offer.basic_economy ? "Yes" : "No"}</span>
              <span><b>Hidden-city</b>{RISK_LABEL[offer.hidden_city]}</span>
              <span><b>Self-transfer</b>{RISK_LABEL[offer.self_transfer]}</span>
            </div>
            <p className={feeCompleteAndKnownRisk ? "offer-confidence" : "offer-confidence offer-confidence-caution"}>
              {COMPARISON_LABEL[offer.comparison_status]}
              {offer.fee_completeness && ` · Fee evidence: ${offer.fee_completeness}`}
            </p>
            <details className="offer-evidence">
            <summary>Price evidence and restrictions</summary>
            <div className="offer-provenance">
              <span>Retrieved {new Date(offer.retrieved_at).toLocaleString()}</span>
              {offer.source_checked_at && <span>Source checked {new Date(offer.source_checked_at).toLocaleString()}</span>}
              {offer.repriced_at && <span>Repriced {new Date(offer.repriced_at).toLocaleString()}</span>}
              {offer.attribution && <span>Source: {offer.attribution}</span>}
              {offer.point_of_sale_country && <span>Point of sale: {offer.point_of_sale_country}</span>}
              {offer.comparable_currency && offer.comparable_currency !== offer.currency_original && (
                <span>
                  Original: {formatMoney(offer.amount_original, offer.currency_original)}
                  {offer.fx_rate ? ` · FX rate ${offer.fx_rate}` : " · FX rate unavailable"}
                  {offer.fx_as_of ? ` · FX as of ${new Date(offer.fx_as_of).toLocaleString()}` : ""}
                </span>
              )}
            </div>
            <FareRiskNotice offer={offer} />
            {offer.warnings.length > 0 && (
              <ul className="offer-warnings">
                {offer.warnings.map((warning, index) => <li key={`${index}-${warning}`}>{warning}</li>)}
              </ul>
            )}
            </details>
          </li>
        );
      })}
    </ul>
  );
}
