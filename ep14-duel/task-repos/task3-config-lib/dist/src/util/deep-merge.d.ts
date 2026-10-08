import type { ConfigObject } from "../types";
/** Recursively merge `patch` over `base`; arrays and scalars are replaced. */
export declare function deepMerge(base: ConfigObject, patch: ConfigObject): ConfigObject;
