import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, TERMINAL_STATUSES, api } from "../api/client";
import type { Job, Results, SortMode } from "../api/types";

const MIN_INTERVAL_MS = 2000;
const MAX_INTERVAL_MS = 10000;

/** Status polling and result snapshots have separate lifecycles. */
export function useJobPolling(jobId: string | null, sort: SortMode, accessVersion = 0) {
  const [job, setJob] = useState<Job | null>(null);
  const [results, setResults] = useState<Results | null>(null);
  const [error, setError] = useState<ApiError | Error | null>(null);
  const [resultsError, setResultsError] = useState<Error | null>(null);
  const [revision, setRevision] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  const generation = useRef(0);
  const resultScope = useRef("");
  const moreInFlight = useRef(false);

  useEffect(() => {
    let alive = true;
    let interval = MIN_INTERVAL_MS;
    let timer: ReturnType<typeof setTimeout> | null = null;
    setJob(null);
    setError(null);
    if (!jobId) return;
    const tick = async () => {
      try {
        const j = await api.getJob(jobId);
        if (!alive) return;
        setJob(j);
        setError(null);
        if (TERMINAL_STATUSES.has(j.status)) return;
      } catch (err) {
        if (alive) setError(err instanceof Error ? err : new Error(String(err)));
      }
      if (!alive) return;
      interval = Math.min(interval + 1000, MAX_INTERVAL_MS);
      timer = setTimeout(tick, interval);
    };
    void tick();
    return () => { alive = false; if (timer) clearTimeout(timer); };
  }, [jobId, accessVersion, revision]);

  const currentJob = job?.job_id === jobId ? job : null;
  const updatedAt = currentJob?.updated_at;
  const status = currentJob?.status;
  useEffect(() => {
    const currentGeneration = ++generation.current;
    const scope = JSON.stringify([jobId, sort, accessVersion]);
    if (resultScope.current !== scope) {
      setResults(null);
      resultScope.current = scope;
    }
    setResultsError(null);
    setLoadingMore(false);
    moreInFlight.current = false;
    if (!jobId || !status) return;
    api.getResults(jobId, sort).then((r) => {
      if (generation.current === currentGeneration) setResults(r);
    }).catch((err) => {
      if (generation.current === currentGeneration) {
        if (err instanceof ApiError && [401, 403, 404, 410].includes(err.status)) setResults(null);
        setResultsError(err instanceof Error ? err : new Error(String(err)));
      }
    });
    return () => { generation.current++; };
  }, [jobId, sort, updatedAt, status, accessVersion, revision]);

  const currentResults = results?.job_id === jobId && results.sort === sort ? results : null;
  // Even terminal jobs need a fresh server snapshot when an observation expires.
  const nextExpiry = currentResults?.next_expiry_at;
  const expiryServerTime = currentResults?.server_time;
  useEffect(() => {
    if (!nextExpiry) return;
    const delay = Date.parse(nextExpiry) - (expiryServerTime ? Date.parse(expiryServerTime) : Date.now());
    if (!Number.isFinite(delay)) return;
    const timer = setTimeout(() => {
      setResults(null); // do not leave an expired price/link visible during the request
      setRevision(value => value + 1);
    }, Math.max(MIN_INTERVAL_MS, Math.min(delay, 2_147_483_647)));
    return () => clearTimeout(timer);
  }, [nextExpiry, expiryServerTime, jobId, sort, accessVersion]);

  const loadMore = useCallback(async () => {
    if (!jobId || !currentResults?.next_cursor || moreInFlight.current) return;
    const currentGeneration = generation.current;
    moreInFlight.current = true;
    setLoadingMore(true);
    setResultsError(null);
    try {
      const page = await api.getResults(jobId, sort, currentResults.next_cursor);
      if (generation.current === currentGeneration) {
        setResults(previous => previous ? {
          ...page,
          itineraries: [...previous.itineraries, ...page.itineraries.filter(
            item => !previous.itineraries.some(old => old.itinerary_id === item.itinerary_id))],
        } : page);
      }
    } catch (err) {
      if (generation.current === currentGeneration) {
        setResultsError(err instanceof Error ? err : new Error(String(err)));
      }
    } finally {
      if (generation.current === currentGeneration) {
        moreInFlight.current = false;
        setLoadingMore(false);
      }
    }
  }, [jobId, sort, currentResults]);

  return { job: currentJob, results: currentResults, error: error ?? resultsError,
           loadMore, loadingMore, retry: () => setRevision(value => value + 1) };
}
