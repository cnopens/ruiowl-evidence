import type { ConfigObject } from "../types";
/** Fail when any of `requiredKeys` is missing from the merged config. */
export declare function validateRequired(config: ConfigObject, requiredKeys: string[]): void;
