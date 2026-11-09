/** FastAPI uses both string details and arrays of field validation errors. */
export function errorMessage(body: unknown, fallback: string): string {
  if (!body || typeof body !== "object" || !("detail" in body)) return fallback;
  const detail = body.detail;
  if (typeof detail === "string") return detail || fallback;
  if (!Array.isArray(detail)) return fallback;
  const messages = detail.flatMap((entry: unknown) => {
    if (!entry || typeof entry !== "object" || !("msg" in entry)) return [];
    return typeof entry.msg === "string" ? [entry.msg] : [];
  });
  return messages.join("; ") || fallback;
}
