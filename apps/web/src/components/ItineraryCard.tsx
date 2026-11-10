import { useId, useState } from "react";
import type { PublicItinerary } from "../api/types";
import { formatMoney } from "../lib/money";
import { flightLocalTime } from "../lib/time";
import { OfferList } from "./OfferList";
import { PriceStatusBadge } from "./PriceStatusBadge";

function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${hours}h ${mins}m`;
}

export function ItineraryCard({ itinerary }: { itinerary: PublicItinerary }) {
  const [expanded, setExpanded] = useState(false);
  const segmentsId = useId();
  const ranked = itinerary.offers.find((o) => o.quote_id === itinerary.ranked_quote_id);
  const displayOffer = ranked ?? itinerary.offers[0];
  const carriers = itinerary.carrier_names?.length ? itinerary.carrier_names : [...new Set(
    itinerary.segments.map(segment => segment.marketing_carrier_name ?? segment.marketing_carrier))];
  const transfers = itinerary.airport_transfers ?? [];
  const flightCode = (carrier: string, number: string) => number.startsWith(carrier) ? number : carrier + number;

  return (
    <article className="itinerary-card">
      <header className="itinerary-header">
        <div className="itinerary-route">
          <span className="route-eyebrow">ONE-WAY FLIGHT</span>
          <h3 className="route-codes">{itinerary.origin} <span aria-hidden="true">→</span> {itinerary.destination}</h3>
          <p className="carrier-summary">{carriers.length ? carriers.join(" · ") : "Airline details unavailable"}</p>
          {itinerary.segments.length > 0 && <span className="flight-numbers">{
            itinerary.segments.map(segment => flightCode(segment.marketing_carrier, segment.flight_number)).join(" · ")
          }</span>}
          <span className="route-date">Departs {flightLocalTime(itinerary.departure_local)}</span>
          <div className="route-chips">
            <span className="route-stops">{itinerary.stops === 0 ? "Nonstop" : `${itinerary.stops} stop${itinerary.stops === 1 ? "" : "s"}`}</span>
            <span className="route-duration">{formatDuration(itinerary.duration_minutes)} total</span>
            <span className="route-arrival">Arrives {flightLocalTime(itinerary.arrival_local)}</span>
          </div>
        </div>
        {displayOffer && (
          <div className="itinerary-pricing">
            <span className="itinerary-price-label">{ranked ? "Quote ranked for this view" : "Available source quote"}</span>
            <strong className="itinerary-best-price">
              {formatMoney(displayOffer.comparable_amount ?? displayOffer.amount_original,
                displayOffer.comparable_currency ?? displayOffer.currency_original)}
            </strong>
            <PriceStatusBadge status={displayOffer.price_status} isEstimate={displayOffer.is_estimate} />
          </div>
        )}
      </header>

      {transfers.length > 0 && <div className="airport-transfer-notice" role="note">
        <strong>Airport change required: </strong>
        {transfers.map(transfer => `${transfer.from_airport} → ${transfer.to_airport}`).join("; ")}.
        Ground transport costs and connection protection are unconfirmed.
      </div>}
      {itinerary.identity_confidence === "insufficient_identity" && (
        <p className="identity-warning">
          Complete flight legs unavailable from this source. These times are a summary, not a confirmed leg-by-leg match.
        </p>
      )}
      {itinerary.warnings && itinerary.warnings.length > 0 && (
        <ul className="itinerary-warnings">
          {itinerary.warnings.map((w, index) => <li key={`${index}-${w}`}>{w}</li>)}
        </ul>
      )}

      {itinerary.segments.length > 0 && (
        <div className="segment-control">
          <button
            type="button"
            className="segments-toggle"
            aria-expanded={expanded}
            aria-controls={segmentsId}
            onClick={() => setExpanded(v => !v)}
          >{expanded ? "Hide flight legs" : `View ${itinerary.segments.length} flight leg${itinerary.segments.length === 1 ? "" : "s"}`}</button>
          <ol className="segments" id={segmentsId} hidden={!expanded}>
            {itinerary.segments.map((segment) => (
              <li key={segment.ordinal}>
                <strong>{segment.origin} → {segment.destination}</strong>
                <span>{segment.marketing_carrier_name ? `${segment.marketing_carrier_name} · ` : ""}
                  {flightCode(segment.marketing_carrier, segment.flight_number)}</span>
                <span>{flightLocalTime(segment.depart_at)} – {flightLocalTime(segment.arrive_at)}</span>
                {segment.operating_carrier !== segment.marketing_carrier &&
                  <span>Operated by {segment.operating_carrier_name ?? segment.operating_carrier}</span>}
              </li>
            ))}
          </ol>
        </div>
      )}

      <div className="offer-section-header">
        <h4>Seller offers <span>({itinerary.offers.length})</span></h4>
        <p>Each price belongs to its own fare and seller.</p>
      </div>
      <OfferList offers={itinerary.offers} rankedQuoteId={itinerary.ranked_quote_id} />
    </article>
  );
}
