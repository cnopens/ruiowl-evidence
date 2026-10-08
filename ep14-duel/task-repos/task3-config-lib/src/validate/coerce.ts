import type { ConfigScalar } from "../types";

/** Coerce a scalar to boolean when the value looks like "true"/"false". */
export function coerceBoolean(value: ConfigScalar): boolean {
  if (typeof value === "boolean") return value;
  if (value === "true") return true;
  if (value === "false") return false;
  throw new Error(`cannot coerce ${JSON.stringify(value)} to boolean`);
}

/** Coerce a scalar to a finite number, throwing on NaN. */
export function coerceNumber(value: ConfigScalar): number {
  const n = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(n)) throw new Error(`cannot coerce ${JSON.stringify(value)} to number`);
  return n;
}
