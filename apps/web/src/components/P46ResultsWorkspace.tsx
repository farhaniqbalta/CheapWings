import { useId, useState } from "react";
import type { PublicItinerary, PublicOffer } from "../api/types";
import { formatMoney } from "../lib/money";
import { flightLocalTime } from "../lib/time";
import { FareRiskNotice } from "./FareRiskNotice";
import { PriceStatusBadge } from "./PriceStatusBadge";

/** A presentation layer only. Respect backend itinerary order and ranked_quote_id. */
type Props = { itineraries: PublicItinerary[] };

function duration(minutes: number): string {
  return `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
}

function flightCode(carrier: string, number: string): string {
  return number.startsWith(carrier) ? number : carrier + number;
}

function carrierNames(itinerary: PublicItinerary): string[] {
  return itinerary.carrier_names?.length ? itinerary.carrier_names : [...new Set(
    itinerary.segments.map(segment => segment.marketing_carrier_name ?? segment.marketing_carrier))];
}

function rankedOffer(itinerary: PublicItinerary): PublicOffer | undefined {
  return itinerary.offers.find(offer => offer.quote_id === itinerary.ranked_quote_id)
    ?? itinerary.offers[0];
}

function money(offer: PublicOffer): string {
  // Keep decimal strings; do not calculate or reprice in the browser.
  return formatMoney(offer.comparable_amount ?? offer.amount_original,
    offer.comparable_currency ?? offer.currency_original);
}

const BAGS = { yes: "Included", no: "Not included", unknown: "Unknown" } as const;
const TRI = { yes: "Yes", no: "No", unknown: "Unknown" } as const;
const STATUS = {
  eligible_total_known: "Comparable total under selected filters",
  extra_cost_unknown: "Possible extra fees — payable total unknown",
  missing_required_baggage: "Required baggage not confirmed in the price",
  ineligible: "Not eligible for the checked ranking",
  currency_unresolved: "Comparable currency unresolved",
} as const;

function describeLink(offer: PublicOffer): string | null {
  if (!offer.link || offer.link_scope === "unavailable") return null;
  if (offer.link_scope === "exact_offer") return "Open exact offer";
  if (offer.link_scope === "itinerary") return "Open itinerary page";
  return "Open source search";
}

function cautionSummary(offer: PublicOffer): string[] {
  const labels: string[] = [];
  if (offer.checked_bag === "unknown") labels.push("Baggage unknown");
  if (offer.checked_bag === "no") labels.push("Bag not included");
  if (offer.hidden_city === "yes") labels.push("Hidden-city risk");
  if (offer.hidden_city === "unknown") labels.push("Hidden-city status unknown");
  if (offer.self_transfer === "yes") labels.push("Self-transfer");
  if (offer.self_transfer === "unknown") labels.push("Transfer protection unknown");
  if (offer.comparison_status !== "eligible_total_known") labels.push(STATUS[offer.comparison_status]);
  return labels;
}

function OfferMatrix({ itinerary }: { itinerary: PublicItinerary }) {
  return (
    <section className="p46-seller-section" aria-labelledby="p46-seller-heading">
      <div className="p46-section-heading">
        <h4 id="p46-seller-heading">Seller offer comparison</h4>
        <span>{itinerary.offers.length} source quote{itinerary.offers.length === 1 ? "" : "s"}</span>
      </div>
      <ul className="p46-seller-list">
        {itinerary.offers.map(offer => {
          const determining = offer.quote_id === itinerary.ranked_quote_id;
          const linkLabel = describeLink(offer);
          const caution = cautionSummary(offer);
          return (
            <li key={offer.quote_id} className={`p46-seller ${determining ? "p46-seller-ranked" : ""}`}>
              <div className="p46-seller-top">
                <div className="p46-seller-name">
                  <strong>{offer.seller ?? "Seller not identified"}</strong>
                  <span>via {offer.provider_id}{offer.fare_family ? ` · ${offer.fare_family}` : ""}</span>
                  {offer.result_origin === "cache" && <span className="p46-cache-note">Observed {new Date(offer.retrieved_at).toLocaleString()} · Cached observation</span>}
                  {offer.result_origin === "shared_inflight" && <span className="p46-cache-note">Shared source observation</span>}
                  {determining && <span className="p46-rank-mark">Quote used for result ordering</span>}
                </div>
                <div className="p46-seller-price">
                  <strong>{money(offer)}</strong>
                  <PriceStatusBadge status={offer.price_status} isEstimate={offer.is_estimate} />
                </div>
              </div>
              <div className="p46-seller-riskline">
                <span>Checked bag: <b>{BAGS[offer.checked_bag]}</b></span>
                {caution.length > 0 ? (
                  <span className="p46-risk-note">{caution.join(" · ")}</span>
                ) : <span className="p46-plain-note">{STATUS[offer.comparison_status]}</span>}
              </div>
              <div className="p46-seller-tools">
                {linkLabel && offer.link ? (
                  <a href={offer.link} target="_blank" rel="noopener noreferrer nofollow"
                    aria-label={`${linkLabel} from ${offer.seller ?? offer.provider_id} (opens new tab)`}>
                    {linkLabel} <span aria-hidden="true">↗</span>
                  </a>
                ) : <span className="p46-link-unavailable">Seller link unavailable</span>}
                {offer.link_scope === "generic_search" && linkLabel &&
                  <span className="p46-link-caveat">Search page, not this confirmed fare</span>}
              </div>
              {offer.warnings.length > 0 && <ul className="p46-quote-warnings p46-quote-warnings-visible">
                {offer.warnings.map((warning, index) => <li key={`${index}-${warning}`}>{warning}</li>)}
              </ul>}
              <details className="p46-offer-evidence">
                <summary>Price evidence and restrictions</summary>
                <div className="p46-evidence-body offer-provenance">
                  <div className="p46-fact-grid">
                    <div><span>Fare type</span><strong>{offer.fare_family ?? "Unknown"}</strong></div>
                    <div><span>Basic economy</span><strong>{offer.basic_economy == null ? "Unknown" : offer.basic_economy ? "Yes" : "No"}</strong></div>
                    <div><span>Hidden-city</span><strong>{TRI[offer.hidden_city]}</strong></div>
                    <div><span>Self-transfer</span><strong>{TRI[offer.self_transfer]}</strong></div>
                    <div><span>Comparison</span><strong>{STATUS[offer.comparison_status]}</strong></div>
                    <div><span>Fee evidence</span><strong>{offer.fee_completeness ?? "Not supplied"}</strong></div>
                  </div>
                  <p className="p46-evidence-line">Retrieved {new Date(offer.retrieved_at).toLocaleString()}</p>
                  {offer.source_checked_at && <p className="p46-evidence-line">Source checked {new Date(offer.source_checked_at).toLocaleString()}</p>}
                  {offer.repriced_at && <p className="p46-evidence-line">Repriced {new Date(offer.repriced_at).toLocaleString()}</p>}
                  {offer.attribution && <p className="p46-evidence-line">Source: {offer.attribution}</p>}
                  {offer.point_of_sale_country && <p className="p46-evidence-line">Point of sale: {offer.point_of_sale_country}</p>}
                  {offer.comparable_currency && offer.comparable_currency !== offer.currency_original && (
                    <p className="p46-evidence-line">Original: {formatMoney(offer.amount_original, offer.currency_original)}
                      {offer.fx_rate ? ` · FX rate ${offer.fx_rate}` : " · FX rate unavailable"}
                      {offer.fx_as_of ? ` · FX as of ${new Date(offer.fx_as_of).toLocaleString()}` : ""}
                    </p>
                  )}
                  <FareRiskNotice offer={offer} />
                </div>
              </details>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

function SelectedDossier({ itinerary }: { itinerary: PublicItinerary }) {
  const [legsOpen, setLegsOpen] = useState(false);
  const legsId = useId();
  const determining = rankedOffer(itinerary);
  return (
    <article className="p46-dossier itinerary-card">
      <div className="p46-dossier-head">
        <div>
          <p className="p46-micro-label">SELECTED ITINERARY / SOURCE EVIDENCE</p>
          <h3>{itinerary.origin} <span aria-hidden="true">→</span> {itinerary.destination}</h3>
          <p className="carrier-summary">{carrierNames(itinerary).join(" · ") || "Airline details unavailable"}</p>
          {itinerary.segments.length > 0 && <span className="flight-numbers">{
            itinerary.segments.map(segment => flightCode(segment.marketing_carrier, segment.flight_number)).join(" · ")
          }</span>}
          <p>{flightLocalTime(itinerary.departure_local)} · {itinerary.stops === 0 ? "Nonstop" : `${itinerary.stops} stop${itinerary.stops === 1 ? "" : "s"}`}</p>
        </div>
        {determining && <div className="p46-dossier-price">
          <span>{itinerary.offers.some(offer => offer.quote_id === itinerary.ranked_quote_id) ? "QUOTE DETERMINING ORDER" : "SOURCE QUOTE"}</span>
          <strong className="itinerary-best-price">{money(determining)}</strong>
          <PriceStatusBadge status={determining.price_status} isEstimate={determining.is_estimate} />
        </div>}
      </div>
      <div className="p46-route-timeline" aria-label="Reported itinerary summary">
        <div><span>DEPARTURE (LOCAL)</span><strong>{flightLocalTime(itinerary.departure_local)}</strong><small>{itinerary.origin}</small></div>
        <div className="p46-timeline-middle"><span>{duration(itinerary.duration_minutes)} TOTAL</span><div className="p46-track" aria-hidden="true"><i/></div><strong>{itinerary.stops === 0 ? "NONSTOP" : `${itinerary.stops} STOP${itinerary.stops > 1 ? "S" : ""}`}</strong></div>
        <div><span>ARRIVAL (LOCAL)</span><strong>{flightLocalTime(itinerary.arrival_local)}</strong><small>{itinerary.destination}</small></div>
      </div>
      {(itinerary.airport_transfers?.length ?? 0) > 0 && <div className="airport-transfer-notice p46-dossier-caution" role="note">
        <strong>Airport change required: </strong>
        {itinerary.airport_transfers!.map(transfer => `${transfer.from_airport} → ${transfer.to_airport}`).join("; ")}.
        Ground transport costs and connection protection are unconfirmed.
      </div>}
      {itinerary.identity_confidence === "insufficient_identity" &&
        <p className="p46-dossier-caution">Full flight-leg identity is unavailable from this source. Do not assume segments, connection protection, or exact time matching.</p>}
      {itinerary.warnings && itinerary.warnings.length > 0 &&
        <ul className="p46-dossier-warnings">{itinerary.warnings.map((w, i) => <li key={`${i}-${w}`}>{w}</li>)}</ul>}
      <OfferMatrix itinerary={itinerary} />
      <section className="p46-leg-section">
        <div className="p46-section-heading"><h4>Flight segments</h4><span>{itinerary.segments.length > 0 ? `${itinerary.segments.length} reported` : "No complete legs supplied"}</span></div>
        {itinerary.segments.length > 0 ? (
          <>
            <button type="button" className="segments-toggle" onClick={() => setLegsOpen(open => !open)}
              aria-expanded={legsOpen} aria-controls={legsId}>
              {legsOpen ? "Hide flight legs" : `View ${itinerary.segments.length} flight leg${itinerary.segments.length === 1 ? "" : "s"}`}
            </button>
            <ol className="p46-leg-list segments" id={legsId} hidden={!legsOpen}>
              {itinerary.segments.map(segment => (
                <li key={segment.ordinal}>
                  <strong>{segment.origin} → {segment.destination}</strong>
                  <span>{segment.marketing_carrier_name ? `${segment.marketing_carrier_name} · ` : ""}{flightCode(segment.marketing_carrier, segment.flight_number)}
                    {segment.operating_carrier !== segment.marketing_carrier ? ` · Operated by ${segment.operating_carrier_name ?? segment.operating_carrier}` : ""}</span>
                  <small>{flightLocalTime(segment.depart_at)} – {flightLocalTime(segment.arrive_at)}</small>
                </li>
              ))}
            </ol>
          </>
        ) : <p className="p46-unknown-legs">Flight-leg detail unavailable. Times above are source summary values.</p>}
      </section>
      <p className="p46-dossier-footnote">CheapWings compares source-reported quotes. Links open external sellers; prices and availability may change.</p>
    </article>
  );
}

export function P46ResultsWorkspace({ itineraries }: Props) {
  const [selectedId, setSelectedId] = useState<string | null>(() => itineraries[0]?.itinerary_id ?? null);
  const selected = itineraries.find(it => it.itinerary_id === selectedId) ?? itineraries[0];
  // Persist the fallback only when identity changes; polling objects alone never reset selection.
  if (selectedId !== (selected?.itinerary_id ?? null)) setSelectedId(selected?.itinerary_id ?? null);
  if (!selected) return null;
  return (
    <div className="p46-workspace" aria-label="Flight comparison workspace">
      <section className="p46-master" aria-label="Itineraries in server result order">
        <div className="p46-ledger-head">
          <div><span className="p46-section-icon" aria-hidden="true">▤</span><h3>Itinerary ledger</h3></div>
          <span>RANKED RESULTS / {itineraries.length} LOADED</span>
        </div>
        <ol className="p46-ledger-list">
          {itineraries.map(itinerary => {
            const offer = rankedOffer(itinerary);
            const active = itinerary.itinerary_id === selected.itinerary_id;
            return (
              <li key={itinerary.itinerary_id}>
                <button type="button" className={`p46-ledger-row ${active ? "is-active" : ""}`}
                  onClick={() => setSelectedId(itinerary.itinerary_id)} aria-pressed={active}
                  aria-label={`Inspect ${itinerary.origin} to ${itinerary.destination}, ${flightLocalTime(itinerary.departure_local)}${offer ? `, ${money(offer)}` : ""}`}>
                  {active && <span className="p46-active-ribbon">● SELECTED ITINERARY / INSPECTING</span>}
                  <span className="p46-ledger-line">
                    <span className="p46-source-square" aria-hidden="true">{(offer?.provider_id ?? "CW").slice(0,2).toUpperCase()}</span>
                    <span className="p46-ledger-route">
                      <strong>{itinerary.origin} <span aria-hidden="true">→</span> {itinerary.destination}</strong>
                      <small>{active ? `via ${offer?.provider_id ?? "unknown source"}` : `${offer?.seller ?? "Seller not identified"}${offer?.provider_id ? ` · via ${offer.provider_id}` : ""}`}</small>
                      {itinerary.identity_confidence === "insufficient_identity" && <em>FLIGHT IDENTITY INCOMPLETE</em>}
                    </span>
                    <span className="p46-ledger-money">
                      <small>{offer ? "SOURCE QUOTE" : "NO QUOTE"}</small>
                      <strong>{offer ? money(offer) : "Unavailable"}</strong>
                    </span>
                  </span>
                  <span className="p46-ledger-under">
                    <span>{flightLocalTime(itinerary.departure_local)}</span>
                    <span className="p46-duration"><span aria-hidden="true" className="p46-short-track"/> {duration(itinerary.duration_minutes)} · {itinerary.stops === 0 ? "NONSTOP" : `${itinerary.stops} STOP${itinerary.stops > 1 ? "S" : ""}`}</span>
                    <span>{flightLocalTime(itinerary.arrival_local)}</span>
                    <span className="p46-inspect-label">{active ? "INSPECTING" : "INSPECT →"}</span>
                  </span>
                  {offer && <span className="p46-ledger-evidence"><PriceStatusBadge status={offer.price_status} isEstimate={offer.is_estimate} />
                    {cautionSummary(offer).length > 0 && <span>Cost / fare conditions need checking</span>}
                  </span>}
                </button>
              </li>
            );
          })}
        </ol>
        <p className="p46-ledger-foot">Results follow the selected ranking. More results may be available via Load more. Inventory completeness remains unknown.</p>
      </section>
      <aside className="p46-detail" aria-label="Selected itinerary detail panel">
        <SelectedDossier key={selected.itinerary_id} itinerary={selected} />
      </aside>
    </div>
  );
}
