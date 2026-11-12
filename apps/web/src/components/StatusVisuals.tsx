import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { ProviderProgress, WorkerPool } from "../api/types";
import { sourceName } from "../lib/sourceNames";

const SEGMENTS = [
  ["succeeded", "done"],
  ["running", "running"],
  ["retry_wait", "retrying"],
  ["pending", "queued"],
  ["failed", "failed"],
  ["cancelled", "cancelled"],
  ["skipped_unsupported", "skipped"],
] as const;

/** One stacked bar per provider for this search; counts are also in the accessible label. */
export function ProviderBars({ statuses }: { statuses: ProviderProgress[] }) {
  if (!statuses.length) return null;
  return (
    <div className="sv-bars">
      {statuses.map(source => {
        const counts = SEGMENTS.map(([key, label]) => [key, label, source[key] ?? 0] as const);
        const total = counts.reduce((sum, [, , n]) => sum + n, 0);
        const summary = counts.filter(([, , n]) => n > 0).map(([, label, n]) => `${n} ${label}`).join(", ");
        return (
          <div className="sv-row" key={source.provider_id}>
            <span className="sv-name">{sourceName(source.provider_id)}</span>
            <span className="sv-bar" role="img" aria-label={`${sourceName(source.provider_id)}: ${summary || "no work"}`}>
              {counts.map(([key, label, n]) => n > 0 && (
                <span key={key} className={`sv-seg sv-${key}`} style={{ flexGrow: n }} title={`${n} ${label}`} />
              ))}
            </span>
            <span className="sv-count">{source.succeeded}/{total}{source.failed > 0 && <em> · {source.failed} failed</em>}</span>
            {source.disabled_reason && <small className="sv-note">disabled: {source.disabled_reason}</small>}
          </div>
        );
      })}
      <p className="sv-legend" aria-hidden="true">
        {SEGMENTS.map(([key, label]) => <span key={key}><i className={`sv-swatch sv-${key}`} />{label}</span>)}
      </p>
    </div>
  );
}

const POLL_MS = 2000;

/** Live shared-pool gauge across all searches; mounted only while the dropdown is open. */
export function PoolGauge() {
  const [pool, setPool] = useState<WorkerPool | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout> | null = null;
    const tick = async () => {
      try {
        const next = await api.workerPool();
        if (!Array.isArray(next?.providers)) throw new Error("Unexpected pool response");
        if (active) { setPool(next); setFailed(false); }
      } catch {
        if (active) setFailed(true);
      }
      if (active) timer = setTimeout(tick, POLL_MS);
    };
    void tick();
    return () => { active = false; if (timer) clearTimeout(timer); };
  }, []);

  if (!pool) return <p className="sv-pool-note">{failed ? "Pool status unavailable." : "Loading worker pool…"}</p>;
  const g = pool.global_capacity;
  const order = new Map(pool.providers.map((p, i) => [p.provider_id, i]));
  const cells = pool.providers.flatMap(p => Array<string>(p.running).fill(p.provider_id));
  const tiers = new Set(pool.providers.map(p => p.priority)).size;
  const reserved = tiers > 1 ? pool.low_priority_headroom : 0;
  const busy = Math.min(pool.running, g);
  const summary = pool.providers.filter(p => p.running).map(p => `${sourceName(p.provider_id)} ${p.running}`).join(", ");
  return (
    <div className="sv-pool">
      <p className="sv-pool-head">
        <strong>Worker pool {busy} / {g} busy</strong>
        {reserved > 0 && <span> · last {reserved} kept free for higher-priority sources</span>}
        {failed && <span className="sv-stale"> · update failed, showing last status</span>}
      </p>
      <div className="sv-cells" role="img" aria-label={`${busy} of ${g} worker slots busy${summary ? `: ${summary}` : ""}`}>
        {Array.from({ length: g }, (_, i) => {
          const pid = cells[i];
          const cls = pid ? `sv-cell sv-p${(order.get(pid) ?? 0) % 6}` : `sv-cell sv-free${i >= g - reserved ? " sv-reserved" : ""}`;
          return <span key={i} className={cls} title={pid ? sourceName(pid) : i >= g - reserved ? "kept free" : "free"} />;
        })}
      </div>
      <ul className="sv-pool-list">
        {pool.providers.map(p => (
          <li key={p.provider_id}>
            <i className={`sv-swatch sv-p${(order.get(p.provider_id) ?? 0) % 6}`} aria-hidden="true" />
            <b>{sourceName(p.provider_id)}</b> {p.running} running · priority {p.priority} ·{" "}
            {p.cooling_down ? <span className="sv-cool">cooldown {Math.ceil(p.wait_ms / 1000)}s</span>
              : p.wait_ms > 0 ? `pacing, next start ${(p.wait_ms / 1000).toFixed(1)}s` : "ready"}
          </li>
        ))}
      </ul>
    </div>
  );
}
