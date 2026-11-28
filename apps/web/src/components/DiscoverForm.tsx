import { useEffect, useId, useState } from "react";
import { ApiError } from "../api/client";
import type { Currency, DiscoverRequest, ProviderCapability } from "../api/types";
import { MAX_DISCOVERY_CALLS, discoveryCallCount } from "../lib/discover";
import { createLocationService } from "../lib/locations";
import type { LocationService } from "../lib/locations";
import { sourceName } from "../lib/sourceNames";
import { AirportMultiSelect } from "./AirportMultiSelect";

interface Props {
  onSubmit: (request: DiscoverRequest) => void;
  submitting: boolean;
  error: ApiError | Error | null;
  supportedCurrencies: string[];
  providers: ProviderCapability[];
  /** False until capabilities have loaded (or after they failed). */
  sourcesKnown: boolean;
}

function todayIso() { return new Date().toISOString().slice(0, 10); }

/** P7.5: origins and a departure window; a discovery source suggests destinations, sources check them. */
export function DiscoverForm({ onSubmit, submitting, error, supportedCurrencies, providers, sourcesKnown }: Props) {
  const [locations, setLocations] = useState<LocationService | null>(null);
  useEffect(() => {
    let active = true;
    fetch(`${import.meta.env.BASE_URL}locations.json`).then(r => { if (!r.ok) throw new Error("Catalog unavailable"); return r.json(); })
      .then(data => { if (active) setLocations(createLocationService(data)); }).catch(() => undefined);
    return () => { active = false; };
  }, []);
  const [origins, setOrigins] = useState<string[]>([]);
  const [from, setFrom] = useState(todayIso());
  const [through, setThrough] = useState(todayIso());
  const [budget, setBudget] = useState("");
  const [displayCurrency, setDisplayCurrency] = useState<Currency>("IDR");
  const [clientError, setClientError] = useState<string | null>(null);
  const id = useId();
  const discoverers = providers.filter(p => p.enabled && p.permitted_to_aggregate === true && p.destination_discovery);
  const checkers = providers.filter(p => p.enabled && p.permitted_to_aggregate === true && p.detailed_search);
  const calls = discoveryCallCount(origins, from, through);
  const overCap = calls > MAX_DISCOVERY_CALLS;
  const budgetValid = budget.trim() === "" || /^\d+(\.\d+)?$/.test(budget.trim()) && Number(budget) > 0;

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setClientError(null);
    if (!origins.length) return setClientError("Add at least one origin airport.");
    if (through < from) return setClientError("Latest departure date cannot be before earliest departure date.");
    if (overCap) return setClientError(`${calls} discovery calls is over the limit of ${MAX_DISCOVERY_CALLS}. Shorten the dates or use fewer origins.`);
    if (!budgetValid) return setClientError("Budget must be a positive number.");
    onSubmit({
      origins, departure_date_from: from, departure_date_through: through, display_currency: displayCurrency,
      budget: budget.trim() || null,
    });
  };

  return (
    <form onSubmit={handleSubmit} aria-label="Discover destinations" className="search-form p46-search-form">
      <div className="p46-console-head">
        <div><span className="p46-console-icon" aria-hidden="true">◎</span><h2>Discover destinations</h2><span className="p46-console-mode">ANYWHERE</span></div>
        <span className="p46-console-meta">ONE-WAY / 1 ADULT / ECONOMY</span>
      </div>
      <div className="p46-console-body">
        <div className="p46-route-section">
          <div className="p46-section-legend"><span>✈</span> FROM <small>Destinations come from the discovery source</small></div>
          <div className="p46-route-fields">
            <AirportMultiSelect label="Origin airports" codes={origins} onChange={codes => setOrigins(codes)} locations={locations} />
          </div>
        </div>
        <div className="p46-parameters">
          <div className="p46-section-legend"><span>▦</span> DEPARTURE WINDOW <small>Inclusive date range</small></div>
          <div className="p46-dates-grid">
            <div className="field">
              <label htmlFor={`${id}-from`}>Earliest departure</label>
              <input id={`${id}-from`} type="date" value={from} min={todayIso()} onChange={e => setFrom(e.target.value)} required />
            </div>
            <div className="field">
              <label htmlFor={`${id}-through`}>Latest departure</label>
              <input id={`${id}-through`} type="date" value={through} min={from} onChange={e => setThrough(e.target.value)} required />
            </div>
            <div className="field">
              <label htmlFor={`${id}-budget`}>Budget (optional, {displayCurrency})</label>
              <input id={`${id}-budget`} inputMode="decimal" value={budget} onChange={e => setBudget(e.target.value)} placeholder="No limit" />
            </div>
            <div className="field">
              <label htmlFor={`${id}-currency`}>Display currency</label>
              <select id={`${id}-currency`} value={displayCurrency} onChange={e => setDisplayCurrency(e.target.value as Currency)}>
                {supportedCurrencies.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>
        </div>
        <p className="discover-sources">
          Destinations from: <b>{sourcesKnown ? discoverers.map(p => sourceName(p.provider_id)).join(", ") || "no discovery source enabled" : "loading sources…"}</b>.
          {" "}Checked with: <b>{checkers.map(p => sourceName(p.provider_id)).join(", ") || "none"}</b>.
        </p>
        <div className="p46-search-footer">
          <div className="p46-query-scope">
            <strong className="combo-preview" aria-live="polite">◉ {calls ? `${calls} discovery calls (max ${MAX_DISCOVERY_CALLS})` : "Add an origin airport and dates"}</strong>
            <span>One call per origin and day. Up to 120 route/dates are then checked, cheapest leads first.</span>
            {overCap && <strong className="field-error">Over the limit of {MAX_DISCOVERY_CALLS} calls; shorten the dates or use fewer origins.</strong>}
          </div>
          <button type="submit" disabled={submitting || overCap || !discoverers.length}>{submitting ? "Starting…" : <>Discover destinations <span aria-hidden="true">→</span></>}</button>
        </div>
      </div>
      <p className="product-limitation">Discovery prices are provisional leads, possibly stale. Only checked fares are fresh source quotes; not every destination is covered.</p>
      {(clientError || error) && <p role="alert" className="field-error">{clientError ?? (error instanceof ApiError ? error.message : "Could not start Discover.")}</p>}
    </form>
  );
}
