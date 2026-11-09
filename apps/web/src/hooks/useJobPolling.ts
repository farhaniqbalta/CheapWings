import { useEffect, useState } from "react";
import { ApiError, TERMINAL_STATUSES, api } from "../api/client";
import type { Job, Results, SortMode } from "../api/types";

const MIN_INTERVAL_MS = 2000;
const MAX_INTERVAL_MS = 10000;
const BACKOFF_STEP_MS = 1000;

/**
 * Polls job status while active (2s, backing off to 10s for long-running
 * jobs, stopping at a terminal status or unmount). Results are refetched
 * independently whenever the job updates or the caller changes sort, so
 * toggling sort never restarts the job-status timer.
 */
export function useJobPolling(jobId: string | null, sort: SortMode) {
  const [job, setJob] = useState<Job | null>(null);
  const [results, setResults] = useState<Results | null>(null);
  const [error, setError] = useState<ApiError | Error | null>(null);

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
        if (TERMINAL_STATUSES.has(j.status)) return; // stop polling, final state reached
      } catch (err) {
        if (alive) setError(err instanceof Error ? err : new Error(String(err)));
      }
      if (!alive) return;
      interval = Math.min(interval + BACKOFF_STEP_MS, MAX_INTERVAL_MS);
      timer = setTimeout(tick, interval);
    };

    void tick();
    return () => {
      alive = false;
      if (timer) clearTimeout(timer);
    };
  }, [jobId]);

  useEffect(() => {
    let alive = true;
    if (!jobId || !job || job.status === "queued") return;
    api
      .getResults(jobId, sort)
      .then((r) => {
        if (alive) setResults(r);
      })
      .catch((err) => {
        // Results can legitimately 410 (expired) independent of job status.
        if (alive) setError(err instanceof Error ? err : new Error(String(err)));
      });
    return () => {
      alive = false;
    };
    // job.updated_at changing is the actual "new data available" signal.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId, sort, job?.updated_at, job?.status]);

  return { job, results, error };
}
