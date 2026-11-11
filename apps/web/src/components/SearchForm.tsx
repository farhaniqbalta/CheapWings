import { useEffect, useId, useState } from "react";
import { ApiError } from "../api/client";
import type { Currency, SearchRequest, ProviderCapability } from "../api/types";
import { AirportMultiSelect } from "./AirportMultiSelect";

import { createLocationService } from "../lib/locations";
import type { LocationService, MajorSelection } from "../lib/locations";
import { planScope } from "../lib/scope";

interface Props {
  onSubmit: (request: SearchRequest) => void;
  submitting: boolean;
  error: ApiError | Error | null;
  maxCombinations: number | null;
  supportedCurrencies: string[];
  providers: ProviderCapability[];
}
function todayIso() { return new Date().toISOString().slice(0, 10); }
/** P4.6 replaces visuals, not the SearchRequest contract or its validation. */
export function SearchForm({ onSubmit, submitting, error, maxCombinations, supportedCurrencies, providers }: Props) {
  const [locations, setLocations] = useState<LocationService | null>(null);
  const [catalogError, setCatalogError] = useState(false);
  const [catalogAttempt, setCatalogAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    fetch(`${import.meta.env.BASE_URL}locations.json`).then(response => {
      if (!response.ok) throw new Error("Catalog unavailable");
      return response.json();
    }).then(data => {if (active) setLocations(createLocationService(data));})
      .catch(() => {if (active) setCatalogError(true);});
    return () => {active = false;};
  }, [catalogAttempt]);
  const [excludedSources, setExcludedSources] = useState<string[]>([]);
  const eligible = providers.filter(p => p.enabled && p.permitted_to_aggregate === true);
  const selectedSources = eligible.filter(p => !excludedSources.includes(p.provider_id)).map(p => p.provider_id);
  const sourceNames: Record<string, string> = {skiplagged: "Skiplagged", swoop: "swoop (Google Flights)", octotrip: "OctoTrip"};
  const [originSelection, setOriginSelection] = useState<MajorSelection | null>(null);
  const [destinationSelection, setDestinationSelection] = useState<MajorSelection | null>(null);
  const [origins, setOrigins] = useState<string[]>([]);
  const [destinations, setDestinations] = useState<string[]>([]);
  const [from, setFrom] = useState(todayIso());
  const [through, setThrough] = useState(todayIso());
  const [maxStops, setMaxStops] = useState<"any" | "0" | "1" | "2">("any");
  const [checkedBagsRequired, setCheckedBagsRequired] = useState(false);
  const [includeBasicEconomy, setIncludeBasicEconomy] = useState(true);
  const [includeHiddenCity, setIncludeHiddenCity] = useState(false);
  const [displayCurrency, setDisplayCurrency] = useState<Currency>("IDR");
  const [clientError, setClientError] = useState<string | null>(null);
  const formId = useId();
  const plan = planScope(origins, destinations, from, through, selectedSources);
  const combos = plan.combinations;
  const overCap = maxCombinations != null && combos > maxCombinations;

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setClientError(null);
    if (origins.length === 0 || destinations.length === 0) {
      setClientError("Add at least one origin and one destination airport.");
      return;
    }
    if (plan.pairs === 0) {
      setClientError("No valid routes. Choose different origin and destination airports.");
      return;
    }
    if (through < from) {
      setClientError("Latest departure date cannot be before earliest departure date.");
      return;
    }
    if (maxCombinations == null) {setClientError("Wait for the server search limit before submitting."); return;}
    if (overCap) {
      setClientError(`${combos} origin x destination x date combinations exceeds the server limit of ${maxCombinations}. Narrow the airports or date range.`);
      return;
    }
    if (!selectedSources.length) {
      setClientError("Select at least one available flight source.");
      return;
    }
    onSubmit({
      ...(originSelection ? {origin_selection:originSelection} : {}),
      ...(destinationSelection ? {destination_selection:destinationSelection} : {}),
      provider_ids: selectedSources,
      origins, destinations,
      departure_date_from: from,
      departure_date_through: through,
      max_stops: maxStops === "any" ? null : (Number(maxStops) as 0 | 1 | 2),
      checked_bags_required: checkedBagsRequired,
      include_basic_economy: includeBasicEconomy,
      include_hidden_city: includeHiddenCity,
      display_currency: displayCurrency,
    });
  };

  return (
    <form onSubmit={handleSubmit} aria-label="Flight search" className="search-form p46-search-form">
      <div className="p46-console-head">
        <div><span className="p46-console-icon" aria-hidden="true">▤</span><h2>Flight query console</h2><span className="p46-console-mode">FLEXIBLE DEPARTURE</span></div>
        <span className="p46-console-meta">ONE-WAY / 1 ADULT / ECONOMY</span>
      </div>
      <div className="p46-console-body">
        {catalogError && <p role="alert">Location catalog unavailable. <button type="button" onClick={() => {setCatalogError(false);setCatalogAttempt(n => n+1);}}>Retry location catalog</button></p>}
        <div className="p46-route-section">
          <div className="p46-section-legend"><span>✈</span> ROUTE SELECTION <small>Multi-airport search supported</small></div>
          <div className="p46-route-fields">
            <AirportMultiSelect label="Origin airports" codes={origins} onChange={(codes, selection) => {setOrigins(codes);setOriginSelection(selection ?? null);}} locations={locations} />
            <AirportMultiSelect label="Destination airports" codes={destinations} onChange={(codes, selection) => {setDestinations(codes);setDestinationSelection(selection ?? null);}} locations={locations} />
          </div>
        </div>
        <div className="p46-parameters">
          <div className="p46-section-legend"><span>▦</span> DEPARTURE WINDOW <small>Inclusive date range</small></div>
          <div className="p46-dates-grid">
            <div className="field">
              <label htmlFor={`${formId}-from`}>Earliest departure</label>
              <input id={`${formId}-from`} type="date" value={from} min={todayIso()}
                onChange={event => setFrom(event.target.value)} required />
            </div>
            <div className="field">
              <label htmlFor={`${formId}-through`}>Latest departure</label>
              <input id={`${formId}-through`} type="date" value={through} min={from}
                onChange={event => setThrough(event.target.value)} required />
            </div>
            <div className="p46-flight-profile"><span>FLIGHT PROFILE</span><strong>Economy <em>·</em> One-way</strong><small>One adult · Available one-way fares only</small></div>
          </div>
        </div>
        <fieldset>
          <legend>Flight sources</legend>
          {providers.map(provider => {
            const available = eligible.some(p => p.provider_id === provider.provider_id);
            return <label className="checkbox" key={provider.provider_id}>
              <input type="checkbox" disabled={!available} checked={available && !excludedSources.includes(provider.provider_id)}
                onChange={event => setExcludedSources(previous => event.target.checked ? previous.filter(id => id !== provider.provider_id) : [...previous, provider.provider_id])} />
              {sourceNames[provider.provider_id] ?? provider.provider_id}
              {!available && <small>{provider.disabled_reason ?? "Source is unavailable or not approved."}</small>}
            </label>;
          })}
          <p>{selectedSources.length} sources selected · Route/date combinations remain independent of source count.</p>
          {!providers.length && <p>Source availability is loading or unavailable. Retry capabilities before searching.</p>}
        </fieldset>
        <div className="p46-preferences">
          <div className="p46-section-legend"><span>☷</span> FARE PREFERENCES</div>
          <div className="p46-checkbox-strip">
            <label className="checkbox"><input type="checkbox" checked={checkedBagsRequired}
              onChange={event => setCheckedBagsRequired(event.target.checked)} />Checked bag required</label>
            <label className="checkbox"><input type="checkbox" checked={includeBasicEconomy}
              onChange={event => setIncludeBasicEconomy(event.target.checked)} />Include basic economy</label>
          </div>
          <details className="p46-advanced">
            <summary>More search settings</summary>
            <div className="p46-advanced-grid">
              <div className="field">
                <label htmlFor={`${formId}-stops`}>Maximum stops</label>
                <select id={`${formId}-stops`} value={maxStops}
                  onChange={event => setMaxStops(event.target.value as typeof maxStops)}>
                  <option value="any">Any</option><option value="0">Nonstop</option>
                  <option value="1">Up to 1 stop</option><option value="2">Up to 2 stops</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor={`${formId}-currency`}>Display currency</label>
                <select id={`${formId}-currency`} value={displayCurrency}
                  onChange={event => setDisplayCurrency(event.target.value as Currency)}>
                  {supportedCurrencies.map(currency => <option key={currency} value={currency}>{currency}</option>)}
                </select>
              </div>
              <label className="checkbox p46-hidden-checkbox"><input type="checkbox" checked={includeHiddenCity}
                onChange={event => setIncludeHiddenCity(event.target.checked)} />Include hidden-city fares</label>
            </div>
            {includeHiddenCity && <p className="warning-text">Hidden-city fares carry airline-enforcement risk and are excluded from the default Best checked deal ranking, even if requested.</p>}
          </details>
        </div>
        <div className="p46-search-footer">
          <div className="p46-query-scope">
            <strong className="combo-preview" aria-live="polite">◉ {origins.length && destinations.length ? `${combos} route-date combinations` : "Add origin and destination airports"}</strong>
            <span>{origins.length} origin airports · {destinations.length} destination airports · {plan.days} dates · Server limit: {maxCombinations ?? "loading"}</span>
            <span>{plan.providerCount} providers · Estimated upper bound: {plan.estimatedWorkItems} provider work items. Cache and provider support can reduce actual calls.</span>
            {!!origins.length && !!destinations.length && plan.pairs === 0 && <strong className="field-error">Same-airport pairs are excluded. Choose airports with at least one valid route.</strong>}
            {overCap && <strong className="field-error">Exceeds the server limit of {maxCombinations}; remove airports, shorten the date range or switch to Specific Airports.</strong>}
          </div>
          <button type="submit" disabled={submitting || overCap || maxCombinations == null}>{submitting ? "Starting search..." : <>Find cheapest flights <span aria-hidden="true">→</span></>}</button>
        </div>
      </div>
      <p className="product-limitation">Source-reported comparison only. Not all flight inventory is covered; displayed prices and booking availability can change.</p>
      {(clientError || error) && <p role="alert" className="field-error">{clientError ??
        (error instanceof ApiError ? error.message : "Could not start the search.")}</p>}
    </form>
  );
}
