/** Preserve the airport-local calendar date and offset supplied by the API. */
export function flightLocalTime(value: string): string {
  const match = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})(?::\d{2}(?:\.\d+)?)?(Z|[+-]\d{2}:\d{2})?$/.exec(value);
  if (!match) return `${value} (unrecognized time)`;
  const [, date, time, offset] = match;
  return `${date} ${time} ${offset ? offset === "Z" ? "UTC" : `UTC${offset}` : "(timezone unknown)"}`;
}
