/**
 * Formats a decimal-string amount with thousands separators WITHOUT parsing
 * through Number, so precision is never at risk from a float round-trip.
 * Display-only; never used for sorting or calculation (the server does that).
 */
export function formatMoney(amountDecimalString: string, currency: string): string {
  const negative = amountDecimalString.startsWith("-");
  const unsigned = negative ? amountDecimalString.slice(1) : amountDecimalString;
  const [whole, fraction] = unsigned.split(".");
  const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  const amount = fraction ? `${grouped}.${fraction}` : grouped;
  return `${negative ? "-" : ""}${currency} ${amount}`;
}
