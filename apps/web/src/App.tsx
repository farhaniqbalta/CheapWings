import { useEffect, useState } from "react";
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

  const isTerminalSuccess = job && (job.status === "completed" || job.status === "partial");
  const zeroEligibleFares = isTerminalSuccess && results && results.itineraries.length === 0;

  return (
    <div className="app">
      <header className="app-header">
        <h1>CheapWings</h1>
        <p>Find the lowest priced eligible one-way flights across flexible dates.</p>
        {capabilities?.synthetic_mode && (
          <p className="synthetic-banner">
            Running in synthetic mode: all results are fake fixtures, not real fares.
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

          <JobErrorPanel job={job} transportError={cancelError ?? pollError} />
          {(pollError || cancelError) && <button type="button" onClick={() => { clearCancelError(); retry(); }}>Retry search status</button>}
          {job && <ResultSortBar sort={sort} onChange={setSort} />}

          {job && (
            <SearchProgress job={job} onCancel={async () => { await cancelSearch(jobId); retry(); }} cancelling={cancelling} />
          )}

          {!job && !pollError && <p aria-live="polite">Loading search...</p>}

          {zeroEligibleFares ? (
            <p className="empty-state">
              No matching fares returned in searched sources. This does not mean no flights exist -
              only the enabled providers were checked. Try Lowest advertised to inspect lower-confidence offers.
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
