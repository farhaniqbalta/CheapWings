import { useEffect, useState } from "react";
import { TERMINAL_STATUSES, api } from "../api/client";
import type { DiscoverJob, Results, SortMode } from "../api/types";

const MIN_INTERVAL_MS = 2000;
const MAX_INTERVAL_MS = 10000;

/** Polls a Discover job until it is terminal; refreshes checked results whenever the job changes. */
export function useDiscoverPolling(jobId: string | null, sort: SortMode, accessVersion = 0) {
  const [job, setJob] = useState<DiscoverJob | null>(null);
  const [results, setResults] = useState<Results | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    let alive = true;
    let interval = MIN_INTERVAL_MS;
    let timer: ReturnType<typeof setTimeout> | null = null;
    if (!jobId) return;
    const tick = async () => {
      try {
        const next = await api.getDiscovery(jobId);
        if (!alive) return;
        setJob(next);
        setError(null);
        if (TERMINAL_STATUSES.has(next.status)) return;
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

  const current = job?.job_id === jobId ? job : null;
  const updatedAt = current?.updated_at;
  const status = current?.status;
  const polls = current ? `${current.succeeded_checks}:${current.discovery.calls_done}` : "";
  useEffect(() => {
    let alive = true;
    if (!jobId || !status) return;
    api.getDiscoveryResults(jobId, sort).then(r => { if (alive) setResults(r); })
      .catch(err => { if (alive) setError(err instanceof Error ? err : new Error(String(err))); });
    return () => { alive = false; };
  }, [jobId, sort, updatedAt, status, polls, accessVersion, revision]);

  return {
    job: current,
    results: results?.job_id === jobId ? results : null,
    error,
    retry: () => setRevision(value => value + 1),
  };
}
