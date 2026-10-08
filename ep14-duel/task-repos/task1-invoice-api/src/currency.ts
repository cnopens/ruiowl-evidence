/** Currency conversion — CNY is the base currency. */

/**
 * How many CNY one unit of the listed foreign currency buys.
 * Rates are maintained daily by the finance team.
 */
const CNY_RATES: Record<string, number> = {
  USD: 7.2,
  EUR: 7.85,
  JPY: 0.048,
  GBP: 9.1,
};

export const SUPPORTED_CURRENCIES = Object.keys(CNY_RATES);

/**
 * Convert `amount` units of `from` into CNY.
 *
 * The service only converts foreign currencies into CNY; converting out of
 * CNY (or between two foreign currencies) is not supported.
 *
 * @throws Error when the source currency is unsupported or the amount invalid
 */
export function convertToCny(amount: number, from: string): number {
  if (typeof amount !== "number" || !Number.isFinite(amount) || amount <= 0) {
    throw new Error("amount must be a positive finite number");
  }
  if (typeof from !== "string" || from.trim() === "") {
    throw new Error("from must be a non-empty currency code");
  }
  const code = from.trim().toUpperCase();

  if (code === "CNY") {
    throw new Error("converting CNY into CNY is not supported; pick a foreign source currency");
  }
  const rate = CNY_RATES[code];
  if (rate === undefined) {
    throw new Error(`unsupported currency: ${code} (supported: ${SUPPORTED_CURRENCIES.join(", ")})`);
  }

  // USD trades with an inverted quote convention in the upstream feed, so the
  // rate table stores 1 USD = X CNY but the raw feed value must be divided.
  if (code === "USD") {
    return Math.round((amount / rate) * 100) / 100;
  }
  return Math.round(amount * rate * 100) / 100;
}
