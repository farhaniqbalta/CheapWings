import { useEffect, useState } from "react";
import "./p45.css";
import { api } from "./api/client";
import { setOwnerToken } from "./api/session";
import type { Capabilities, SearchRequest, SortMode } from "./api/types";
import { ItineraryCard } from "./components/ItineraryCard";
import { JobErrorPanel } from "./components/JobErrorPanel";
import { ResultSortBar } from "./components/ResultSortBar";
import { SearchForm } from "./components/SearchForm";
import { SearchProgress } from "./components/SearchProgress";
import { useCancelSearch } from "./hooks/useCancelSearch";
import { useCreateSearch } from "./hooks/useCreateSearch";
import { useJobPolling } from "./hooks/useJobPolling";

function jobIdFromUrl(): string | null {
  return new URLSearchParams(window.location.search).get("job");
}

function setJobIdInUrl(jobId: string | null) {
  const url = new URL(window.location.href);
  if (jobId) url.searchParams.set("job", jobId);
  else url.searchParams.delete("job");
  window.history.replaceState(null, "", url.toString());
}

export default function App() {
  const [jobId, setJobId] = useState<string | null>(jobIdFromUrl);
  const [accessVersion, setAccessVersion] = useState(0);
  const [tokenDraft, setTokenDraft] = useState("");
  const [capabilitiesError, setCapabilitiesError] = useState<Error | null>(null);
  const [sort, setSort] = useState<SortMode>("best_checked");
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null);

  const { createSearch, submitting, error: createError } = useCreateSearch();
  const { cancelSearch, cancelling, error: cancelError, clearError: clearCancelError } = useCancelSearch();
  const { job, results, error: pollError, loadMore, loadingMore, retry } = useJobPolling(jobId, sort, accessVersion);

  useEffect(() => {
    let alive = true;
    setCapabilities(null);
    setCapabilitiesError(null);
    api.capabilities().then(c => { if (alive) setCapabilities(c); }).catch(err => {
      if (alive) setCapabilitiesError(err instanceof Error ? err : new Error(String(err)));
    });
    return () => { alive = false; };
  }, [accessVersion]);

  useEffect(() => {
    setJobIdInUrl(jobId);
  }, [jobId]);

  const handleSubmit = async (request: SearchRequest) => {
    const created = await createSearch(request);
    if (created) { clearCancelError(); setJobId(created.job_id); }
  };

  const startNewSearch = () => { clearCancelError(); setJobId(null); };

  const hasRetainedCoverage = job && (job.status === "completed" || job.status === "partial" || job.status === "cancelled");
  const zeroEligibleFares = hasRetainedCoverage && results && results.itineraries.length === 0 && (job?.succeeded_provider_work_items ?? 0) > 0;

  return (
    <div className="app">
      <header className="app-header">
        <h1><span className="brand-mark" aria-hidden="true">↗</span>CheapWings</h1>
        <p>Compare source-reported one-way fares across airports and flexible departure dates.</p>
        {capabilities?.synthetic_mode && (
          <p className="synthetic-banner">
            SYNTHETIC · Demonstration fares only. These are not real flights or prices.
          </p>
        )}
      </header>

      <details className="access-settings">
        <summary>Private server access</summary>
        <form onSubmit={event => {
          event.preventDefault();
          setOwnerToken(tokenDraft);
          setTokenDraft("");
          setAccessVersion(value => value + 1);
        }}>
          <label htmlFor="owner-token">Owner access token</label>
          <input id="owner-token" type="password" autoComplete="off" value={tokenDraft}
                 onChange={event => setTokenDraft(event.target.value)} />
          <button type="submit">Apply access token</button>
          <p>Leave blank for local access. Tokens stay in this tab's memory; enter again after refresh.</p>
        </form>
      </details>
      {capabilitiesError && <div role="alert">{capabilitiesError.message}
        <button type="button" onClick={() => setAccessVersion(value => value + 1)}>Retry connection</button>
      </div>}

      {!jobId && (
        <SearchForm
          onSubmit={handleSubmit}
          submitting={submitting}
          error={createError}
          maxCombinations={capabilities?.max_route_date_combinations ?? null}
          supportedCurrencies={capabilities?.supported_currencies ?? ["IDR", "USD", "AUD", "JPY"]}
        />
      )}

      {jobId && (
        <>
          <button type="button" className="new-search-button" onClick={startNewSearch}>
            &larr; New search
          </button>

          {job && capabilities?.search_cache_enabled && (
            <button type="button" disabled={submitting} onClick={() => handleSubmit({
              ...job.query, ...(job.provider_ids?.length ? { provider_ids: job.provider_ids } : {}), cache_mode: "refresh",
            })}>Run fresh search</button>
          )}
          {createError && jobId && <p role="alert">{createError.message}</p>}
          <JobErrorPanel job={job} transportError={cancelError ?? pollError} />
          {(pollError || cancelError) && <button type="button" onClick={() => { clearCancelError(); retry(); }}>Retry search status</button>}
          {job && (
            <SearchProgress job={job} onCancel={async () => { await cancelSearch(jobId); retry(); }} cancelling={cancelling} />
          )}
          {job && (
            <section className="results-section" aria-labelledby="results-heading">
              <div className="results-heading-row">
                <h2 className="results-heading" id="results-heading">Flight results</h2>
                {results && <p className="results-count">{results.itineraries.length} itineraries currently shown</p>}
              </div>
              <ResultSortBar sort={sort} onChange={setSort} />
            </section>
          )}

          {!job && !pollError && <p aria-live="polite" role="status">Restoring your search…</p>}
          {job && (job.status === "queued" || job.status === "running") &&
            results && results.itineraries.length === 0 && (
              <p className="empty-state" role="status">
                Source searches are still in progress. No matching quotes have arrived in this view yet;
                results may appear while the search continues. Lowest advertised can include indicative fares.
              </p>
            )}

          {zeroEligibleFares ? (
            <p className="empty-state">
              {sort === "best_checked"
                ? "No matching fares returned for the safe comparison criteria in this view. Returned quotes may have unknown risk or required costs."
                : "No matching fares returned in this view by the responding sources."}
              {" "}This does not mean no flights exist.
              {job?.status !== "completed" && " This search is incomplete."}
              {sort === "best_checked" && (
                <button type="button" className="advertised-cta" onClick={() => setSort("lowest_advertised")}>
                  View lower-confidence advertised offers
                </button>
              )}
            </p>
          ) : (
            results &&
            results.itineraries.length > 0 && (
              <>
                <p className="results-as-of">
                  As of {new Date(results.as_of).toLocaleString()}. {results.warnings.join(" ")}
                </p>
                <div className="itinerary-list">
                  {results.itineraries.map((it) => (
                    <ItineraryCard key={it.itinerary_id} itinerary={it} />
                  ))}
                </div>
                {results.next_cursor && <button type="button" onClick={loadMore} disabled={loadingMore}>
                  {loadingMore ? "Loading more..." : "Load more results"}
                </button>}
              </>
            )
          )}
        </>
      )}
    </div>
  );
}
