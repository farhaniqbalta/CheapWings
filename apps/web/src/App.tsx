import { useEffect, useRef, useState } from "react";
import "./p46.css";
import { api } from "./api/client";
import { setOwnerToken } from "./api/session";
import type { Capabilities, DiscoverRequest, SearchRequest, SortMode } from "./api/types";
import { DiscoverForm } from "./components/DiscoverForm";
import { DiscoverView } from "./components/DiscoverView";
import { useDiscoverPolling } from "./hooks/useDiscoverPolling";
import { P46ResultsWorkspace } from "./components/P46ResultsWorkspace";
import { ExpiredFareCard } from "./components/ExpiredFareCard";
import { JobErrorPanel } from "./components/JobErrorPanel";
import { ResultSortBar } from "./components/ResultSortBar";
import { SearchForm } from "./components/SearchForm";
import { P46SearchProgress } from "./components/P46SearchProgress";
import { useCancelSearch } from "./hooks/useCancelSearch";
import { useCreateSearch } from "./hooks/useCreateSearch";
import { useJobPolling } from "./hooks/useJobPolling";

function jobIdFromUrl(key = "job"): string | null {
  return new URLSearchParams(window.location.search).get(key);
}

function setJobIdInUrl(jobId: string | null, key = "job") {
  const url = new URL(window.location.href);
  if (jobId) url.searchParams.set(key, jobId);
  else url.searchParams.delete(key);
  window.history.replaceState(null, "", url.toString());
}

export default function App() {
  const [jobId, setJobId] = useState<string | null>(jobIdFromUrl);
  // P7.5: Discover is a separate mode with its own job id (?discover=<id>).
  const [discoverId, setDiscoverId] = useState<string | null>(() => jobIdFromUrl("discover"));
  const [discoverSubmitting, setDiscoverSubmitting] = useState(false);
  const [discoverError, setDiscoverError] = useState<Error | null>(null);
  const [discoverCancelling, setDiscoverCancelling] = useState(false);
  const [accessVersion, setAccessVersion] = useState(0);
  const [tokenDraft, setTokenDraft] = useState("");
  const [capabilitiesError, setCapabilitiesError] = useState<Error | null>(null);
  const [sort, setSort] = useState<SortMode>("lowest_advertised");
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null);

  const { createSearch, submitting, error: createError } = useCreateSearch();
  const { cancelSearch, cancelling, error: cancelError, clearError: clearCancelError } = useCancelSearch();
  const [mode, setMode] = useState<"search" | "discover">(() => jobIdFromUrl("discover") ? "discover" : "search");
  const { job, results, error: pollError, loadMore, loadingMore, retry } = useJobPolling(mode === "search" ? jobId : null, sort, accessVersion);

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
  useEffect(() => {
    setJobIdInUrl(discoverId, "discover");
  }, [discoverId]);
  const modeRef = useRef(mode);
  useEffect(() => { modeRef.current = mode; }, [mode]);
  const discover = useDiscoverPolling(mode === "discover" ? discoverId : null, sort, accessVersion);

  const handleDiscover = async (request: DiscoverRequest) => {
    setDiscoverSubmitting(true);
    setDiscoverError(null);
    try {
      const created = await api.createDiscovery(request);
      // Switched to Search while starting: don't jump back (the run continues on the server).
      if (modeRef.current === "discover") setDiscoverId(created.job_id);
    } catch (err) {
      setDiscoverError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setDiscoverSubmitting(false);
    }
  };
  const cancelDiscover = async () => {
    if (!discoverId) return;
    setDiscoverCancelling(true);
    try { await api.cancelDiscovery(discoverId); discover.retry(); }
    catch (err) { setDiscoverError(err instanceof Error ? err : new Error(String(err))); }
    finally { setDiscoverCancelling(false); }
  };
  // Each mode keeps its own job; switching only changes which one is shown.
  const chooseMode = (next: "search" | "discover") => {
    if (next !== mode) setMode(next);
  };

  const handleSubmit = async (request: SearchRequest) => {
    const created = await createSearch(request);
    if (created) { clearCancelError(); setJobId(created.job_id); }
  };

  const startNewSearch = () => { clearCancelError(); setJobId(null); };

  const hasRetainedCoverage = job && (job.status === "completed" || job.status === "partial" || job.status === "cancelled");
  const zeroEligibleFares = hasRetainedCoverage && results && !results.expired_observations?.length && results.itineraries.length === 0 && (job?.succeeded_provider_work_items ?? 0) > 0;

  return (
    <div className="app">
      <header className="app-header">
        <div className="p46-header-line">
          <div className="p46-brand"><h1>CHEAPWINGS</h1><span className="p46-brand-sub">◉ SOURCE-REPORTED FARES</span></div>
          <div className="p46-header-nav">
            <span className="p46-mode-toggle" role="group" aria-label="Search or Discover">
              <button type="button" aria-pressed={mode === "search"} onClick={() => chooseMode("search")}>Search</button>
              <button type="button" aria-pressed={mode === "discover"} onClick={() => chooseMode("discover")}>Discover</button>
            </span>
            {mode === "search" && <span className="p46-header-active">{jobId ? "FARE RESULTS" : "FLIGHT SEARCH"}</span>}
            {mode === "discover" && discoverId && <button type="button" className="new-search-button p46-header-action" onClick={() => setDiscoverId(null)}>
              &larr; New Discover
            </button>}
            {mode === "search" && jobId && <>
          <button type="button" className="new-search-button p46-header-action" onClick={startNewSearch}>
            &larr; New search
          </button>

          {job && (
            <button type="button" className="p46-header-action" disabled={submitting} onClick={() => handleSubmit({
              ...job.query, ...(job.provider_ids?.length ? { provider_ids: job.provider_ids } : {}), cache_mode: "refresh",
            })}>Run fresh search</button>
          )}
            </>}
            {mode === "search" && !jobId && <span>FLEXIBLE DATES</span>}
            <span className="p46-header-muted">ONE-WAY · ECONOMY</span>
          </div>
        </div>
        <div className="p46-meta-bar">
          <span className="p46-meta-tag">CHEAPWINGS // OBSIDIAN AMBER</span>
          {mode === "search" && job?.query && <>
            <span>ROUTE: <b>{job.query.origins.join(", ")} → {job.query.destinations.join(", ")}</b></span>
            <span>WINDOW: <b>{job.query.departure_date_from} – {job.query.departure_date_through}</b></span>
            <span>CURRENCY: <b>{job.query.display_currency ?? "IDR"}</b></span>
          </>}
          <span>SCOPE: <b>ENABLED SOURCES ONLY</b></span>
          {capabilities?.synthetic_mode && <span className="synthetic-banner">SYNTHETIC · Demonstration fares only. These are not real flights or prices.</span>}
        </div>
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

      {mode === "discover" && !discoverId && (
        <DiscoverForm
          onSubmit={handleDiscover}
          submitting={discoverSubmitting}
          error={discoverError}
          providers={capabilities?.providers ?? []}
          supportedCurrencies={capabilities?.supported_currencies ?? ["IDR", "USD", "AUD", "JPY"]}
          sourcesKnown={capabilities !== null}
        />
      )}

      {mode === "discover" && discoverId && (
        <>
          {(discover.error || discoverError) && <div role="alert">{(discover.error ?? discoverError)!.message}
            <button type="button" onClick={() => { setDiscoverError(null); discover.retry(); }}>Retry Discover status</button></div>}
          {!discover.job && !discover.error && <p aria-live="polite" role="status">Restoring Discover…</p>}
          {discover.job && <DiscoverView job={discover.job} onCancel={cancelDiscover} cancelling={discoverCancelling} />}
          {discover.results && discover.results.itineraries.length > 0 && (
            <section className="results-section" aria-labelledby="discover-results-heading">
              <div className="results-heading-row">
                <h2 className="results-heading" id="discover-results-heading">Checked fares</h2>
                <p className="results-count">{discover.results.itineraries.length} itineraries</p>
              </div>
              <ResultSortBar sort={sort} onChange={setSort} />
              <P46ResultsWorkspace key={`${discoverId}:${sort}`} itineraries={discover.results.itineraries} />
            </section>
          )}
        </>
      )}

      {mode === "search" && !jobId && (
        <SearchForm
          onSubmit={handleSubmit}
          submitting={submitting}
          error={createError}
          maxCombinations={capabilities?.max_route_date_combinations ?? null}
          providers={capabilities?.providers ?? []}
          supportedCurrencies={capabilities?.supported_currencies ?? ["IDR", "USD", "AUD", "JPY"]}
        />
      )}

      {mode === "search" && jobId && (
        <>
          {createError && jobId && <p role="alert">{createError.message}</p>}
          <JobErrorPanel job={job} transportError={cancelError ?? pollError} />
          {(pollError || cancelError) && <button type="button" onClick={() => { clearCancelError(); retry(); }}>Retry search status</button>}
          {job && (
            <P46SearchProgress job={job} onCancel={async () => { await cancelSearch(jobId); retry(); }} cancelling={cancelling} />
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
            results && !results.expired_observations?.length && results.itineraries.length === 0 && (
              <p className="empty-state" role="status">
                Source searches are still in progress. No matching quotes have arrived in this view yet;
                results may appear while the search continues. Lowest advertised can include indicative fares.
              </p>
            )}

          {!!results?.expired_observations?.length && <section aria-label="Expired fare observations">
            <h2>Expired fare observations</h2>
            {job?.status === "running" && <p>Other source searches are still progressing.</p>}
            {results.expired_observations.map(observation => <ExpiredFareCard
              key={`${observation.provider_id}:${observation.origin}:${observation.destination}:${observation.departure_date}`}
              observation={observation} refreshing={submitting}
              onRefresh={() => { if (job) void handleSubmit({...job.query, provider_ids:job.provider_ids, cache_mode:"refresh"}); }} />)}
          </section>}

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
                <P46ResultsWorkspace key={`${jobId}:${sort}`} itineraries={results.itineraries} />
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
