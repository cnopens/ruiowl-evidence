import type { ConfigSourceOptions } from "../options";
export declare function warmCache(options?: ConfigSourceOptions): Promise<number>;
/** Number of independent ConfigSource instances the warmer keeps alive. */
export declare const WARMER_INSTANCES = 3;
