import { useId, useMemo, useState } from "react";
import { ApiError } from "../api/client";
import type { Currency, SearchRequest } from "../api/types";
import { AirportMultiSelect } from "./AirportMultiSelect";

interface Props {
  onSubmit: (request: SearchRequest) => void;
  submitting: boolean;
  error: ApiError | Error | null;
  maxCombinations: number | null;
  supportedCurrencies: string[];
}

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function combinationCount(origins: string[], destinations: string[], from: string, through: string) {
  if (!from || !through) return 0;
  const start = new Date(`${from}T00:00:00Z`);
  const end = new Date(`${through}T00:00:00Z`);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || end < start) return 0;
  const days = Math.round((end.getTime() - start.getTime()) / 86_400_000) + 1;
  // Illustrative preview only; the server is the source of truth and also
  // rejects same-origin/destination pairs on submit.
  return origins.length * destinations.length * days;
}

export function SearchForm({ onSubmit, submitting, error, maxCombinations, supportedCurrencies }: Props) {
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
  const combos = useMemo(
    () => combinationCount(origins, destinations, from, through),
    [origins, destinations, from, through],
  );
  const overCap = maxCombinations != null && combos > maxCombinations;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setClientError(null);
    if (origins.length === 0 || destinations.length === 0) {
      setClientError("Add at least one origin and one destination airport.");
      return;
    }
    if (origins.some((o) => destinations.includes(o))) {
      setClientError("Origin and destination airports cannot overlap.");
      return;
    }
    if (through < from) {
      setClientError("Latest departure date cannot be before earliest departure date.");
      return;
    }
    if (overCap) {
      setClientError(
        `${combos} origin x destination x date combinations exceeds the server limit of ${maxCombinations}. Narrow the airports or date range.`,
      );
      return;
    }
    onSubmit({
      origins,
      destinations,
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
    <form onSubmit={handleSubmit} aria-label="Flight search" className="search-form">
      <p className="product-limitation">
        Finds the lowest eligible one-way fare <strong>found by the enabled providers</strong> across
        flexible dates. One-way, 1 adult, economy. Not the world's cheapest ticket, and not a
        guarantee of availability.
      </p>

      <p className="form-section-caption">01 · Route and dates</p>
      <div className="field-row">
        <AirportMultiSelect label="From" codes={origins} onChange={setOrigins} />
        <AirportMultiSelect label="To" codes={destinations} onChange={setDestinations} />
      </div>

      <div className="field-row">
        <div className="field">
          <label htmlFor={`${formId}-from`}>Earliest departure</label>
          <input
            id={`${formId}-from`}
            type="date"
            value={from}
            min={todayIso()}
            onChange={(e) => setFrom(e.target.value)}
            required
          />
        </div>
        <div className="field">
          <label htmlFor={`${formId}-through`}>Latest departure</label>
          <input
            id={`${formId}-through`}
            type="date"
            value={through}
            min={from}
            onChange={(e) => setThrough(e.target.value)}
            required
          />
        </div>
      </div>

      <p className="form-section-caption">02 · Fare preferences</p>
      <div className="field-row">
        <div className="field">
          <label htmlFor={`${formId}-stops`}>Max stops</label>
          <select
            id={`${formId}-stops`}
            value={maxStops}
            onChange={(e) => setMaxStops(e.target.value as typeof maxStops)}
          >
            <option value="any">Any</option>
            <option value="0">Nonstop</option>
            <option value="1">1 stop</option>
            <option value="2">2 stops</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor={`${formId}-currency`}>Currency</label>
          <select
            id={`${formId}-currency`}
            value={displayCurrency}
            onChange={(e) => setDisplayCurrency(e.target.value as Currency)}
          >
            {supportedCurrencies.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="field-row checkboxes">
        <label className="checkbox">
          <input
            type="checkbox"
            checked={checkedBagsRequired}
            onChange={(e) => setCheckedBagsRequired(e.target.checked)}
          />
          Checked bag required
        </label>
        <label className="checkbox">
          <input
            type="checkbox"
            checked={includeBasicEconomy}
            onChange={(e) => setIncludeBasicEconomy(e.target.checked)}
          />
          Include basic economy
        </label>
      </div>

      <div className="field hidden-city-field">
        <label className="checkbox">
          <input
            type="checkbox"
            checked={includeHiddenCity}
            onChange={(e) => setIncludeHiddenCity(e.target.checked)}
          />
          Include hidden-city fares
        </label>
        {includeHiddenCity && (
          <p className="warning-text">
            Hidden-city fares skip part of your ticketed itinerary and carry airline-enforcement
            risk (lost status, cancelled return legs). They are never included in the default
            "Best checked deal" ranking even when enabled here.
          </p>
        )}
      </div>

      <p className="combo-preview" aria-live="polite">
        {combos > 0
          ? `${combos} origin x destination x date combination${combos === 1 ? "" : "s"}.`
          : "Add airports and dates to see how many combinations will be searched."}
        {overCap && (
          <span className="field-error">
            {" "}
            Exceeds the server limit of {maxCombinations}; narrow your search.
          </span>
        )}
        {" A search may take time; results can arrive while it runs."}
      </p>

      {(clientError || error) && (
        <p role="alert" className="field-error">
          {clientError ?? (error instanceof ApiError ? error.message : "Could not start the search.")}
        </p>
      )}

      <button type="submit" disabled={submitting || overCap}>
        {submitting ? "Starting search..." : "Find cheapest flights"}
      </button>
    </form>
  );
}
