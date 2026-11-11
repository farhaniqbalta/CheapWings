/** Same valid-pair semantics as domain/scope.py and backend expansion. */
export function planScope(origins: string[], destinations: string[], from: string, through: string, providers: string[]) {
  const unique = (codes: string[]) => [...new Set(codes.map(c => c.trim().toUpperCase()))];
  const o = unique(origins), d = unique(destinations);
  const start = Date.parse(`${from}T00:00:00Z`), end = Date.parse(`${through}T00:00:00Z`);
  const days = Number.isFinite(start) && Number.isFinite(end) ? Math.max(0, Math.round((end-start)/86400000)+1) : 0;
  const pairs = o.length*d.length-o.filter(code => d.includes(code)).length;
  const combinations = pairs*days;
  const providerCount = new Set(providers).size;
  return {days, pairs, combinations, providerCount, estimatedWorkItems:combinations*providerCount};
}
