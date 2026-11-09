import { useEffect, useState } from "react";
import { api } from "./api/client";
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
  const [sort, setSort] = useState<SortMode>("best_checked");
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null);

  const { createSearch, submitting, error: createError } = useCreateSearch();
  const { cancelSearch, cancelling } = useCancelSearch();
  const { job, results, error: pollError } = useJobPolling(jobId, sort);

  useEffect(() => {
    api.capabilities().catch(() => undefined).then((c) => c && setCapabilities(c));
  }, []);

  useEffect(() => {
    setJobIdInUrl(jobId);
  }, [jobId]);

  const handleSubmit = async (request: SearchRequest) => {
    const created = await createSearch(request);
    if (created) setJobId(created.job_id);
  };

  const startNewSearch = () => setJobId(null);

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

          <JobErrorPanel job={job} transportError={pollError} />

          {job && (
            <SearchProgress job={job} onCancel={() => cancelSearch(jobId)} cancelling={cancelling} />
          )}

          {!job && !pollError && <p aria-live="polite">Loading search...</p>}

          {job?.status === "failed" ? null : zeroEligibleFares ? (
            <p className="empty-state">
              No matching fares returned in searched sources. This does not mean no flights exist -
              only the enabled providers were checked.
            </p>
          ) : (
            results &&
            results.itineraries.length > 0 && (
              <>
                <ResultSortBar sort={sort} onChange={setSort} />
                <p className="results-as-of">
                  As of {new Date(results.as_of).toLocaleString()}. {results.warnings.join(" ")}
                </p>
                <div className="itinerary-list">
                  {results.itineraries.map((it) => (
                    <ItineraryCard key={it.itinerary_id} itinerary={it} />
                  ))}
                </div>
              </>
            )
          )}
        </>
      )}
    </div>
  );
}
