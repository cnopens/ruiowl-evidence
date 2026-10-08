import type { ConfigObject } from "./types";
/**
 * Options accepted by {@link ConfigSource}.
 *
 * Layers are merged in order of increasing precedence:
 * defaults < file < environment.
 */
export interface ConfigSourceOptions {
    /** Path to an optional JSON/YAML config file. */
    file?: string;
    /** Environment variable prefix, e.g. "APP" reads APP_PORT, APP_LOG_LEVEL. */
    envPrefix?: string;
    /** Built-in defaults applied first. */
    defaults?: ConfigObject;
    /** Milliseconds to cache the merged result; 0 disables caching. */
    cacheMs?: number;
    /** When set, the loader requires every schema key to be present. */
    required?: string[];
}
export declare const DEFAULT_OPTIONS: Readonly<ConfigSourceOptions>;
export declare function resolveOptions(input: ConfigSourceOptions | undefined): Required<ConfigSourceOptions>;
