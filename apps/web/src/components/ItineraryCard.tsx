import { useState } from "react";
import type { PublicItinerary } from "../api/types";
import { OfferList } from "./OfferList";

function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${h}h ${m}m`;
}

export function ItineraryCard({ itinerary }: { itinerary: PublicItinerary }) {
  const [expanded, setExpanded] = useState(false);
  const depart = new Date(itinerary.departure_local);
  const best = itinerary.offers.find((o) => o.quote_id === itinerary.ranked_quote_id) ?? itinerary.offers[0];

  return (
    <article className="itinerary-card">
      <header className="itinerary-header">
        <div className="itinerary-route">
          <span className="route-codes">
            {itinerary.origin} &rarr; {itinerary.destination}
          </span>
          <span className="route-date">
            {depart.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })}
          </span>
          <span className="route-stops">{itinerary.stops === 0 ? "Nonstop" : `${itinerary.stops} stop${itinerary.stops > 1 ? "s" : ""}`}</span>
          <span className="route-duration">{formatDuration(itinerary.duration_minutes)}</span>
        </div>
        {best && (
          <span className="itinerary-best-price">
            {best.comparable_amount ?? best.amount_original} {best.comparable_currency ?? best.currency_original}
          </span>
        )}
      </header>

      {itinerary.identity_confidence === "insufficient_identity" && (
        <p className="identity-warning">
          Full flight-segment detail unavailable from this source; route and timing are approximate and
          not matched against other providers' itineraries.
        </p>
      )}
      {itinerary.warnings && itinerary.warnings.length > 0 && (
        <ul className="itinerary-warnings">
          {itinerary.warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}

      {itinerary.segments.length > 0 && (
        <button
          type="button"
          className="segments-toggle"
          aria-expanded={expanded}
          onClick={() => setExpanded((v) => !v)}
        >
          {expanded ? "Hide flight details" : "Show flight details"}
        </button>
      )}
      {expanded && (
        <ol className="segments">
          {itinerary.segments.map((s) => (
            <li key={s.ordinal}>
              {s.marketing_carrier}
              {s.flight_number} {s.origin}&rarr;{s.destination}
              {" "}({new Date(s.depart_at).toLocaleTimeString()} - {new Date(s.arrive_at).toLocaleTimeString()})
              {s.operating_carrier !== s.marketing_carrier ? ` operated by ${s.operating_carrier}` : ""}
            </li>
          ))}
        </ol>
      )}

      <h3 className="sr-only">Offers for {itinerary.origin} to {itinerary.destination}</h3>
      <OfferList offers={itinerary.offers} rankedQuoteId={itinerary.ranked_quote_id} />
    </article>
  );
}
