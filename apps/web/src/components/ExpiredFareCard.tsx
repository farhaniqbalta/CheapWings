import type { ExpiredObservation } from "../api/types";

export function ExpiredFareCard({ observation, onRefresh, refreshing }: {
  observation: ExpiredObservation; onRefresh: () => void; refreshing: boolean;
}) {
  return <article className="expired-fare-card" aria-label={`Expired fares from ${observation.provider_id}`}>
    <strong className="expired-fare-badge">Expired · Price details unavailable</strong>
    <h3>{observation.origin} → {observation.destination} · {observation.departure_date}</h3>
    <p>Source: {observation.provider_id}</p>
    {observation.observed_at ? <p>Originally observed: <time dateTime={observation.observed_at}>{new Date(observation.observed_at).toLocaleString()}</time></p> : <p>Original observation time unavailable.</p>}
    <p>Expired: <time dateTime={observation.expired_at}>{new Date(observation.expired_at).toLocaleString()}</time></p>
    <p>These prices are no longer current. Fare details are no longer retained under the current retention policy. Your search record and coverage remain available.</p>
    <button type="button" disabled={refreshing} onClick={onRefresh}>Run fresh search</button>
  </article>;
}
