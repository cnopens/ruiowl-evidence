import type { ConfigScalar } from "../types";
/** Coerce a scalar to boolean when the value looks like "true"/"false". */
export declare function coerceBoolean(value: ConfigScalar): boolean;
/** Coerce a scalar to a finite number, throwing on NaN. */
export declare function coerceNumber(value: ConfigScalar): number;
