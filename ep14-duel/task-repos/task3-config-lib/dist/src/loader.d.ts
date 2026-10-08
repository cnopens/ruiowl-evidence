import { ConfigSourceOptions } from "./options";
import type { ConfigObject } from "./types";
/**
 * Loads configuration from layered sources with optional caching.
 *
 * Usage:
 * ```ts
 * const loader = new ConfigSource({ file: "./app.json", envPrefix: "APP" });
 * const cfg = await loader.load();
 * ```
 */
export declare class ConfigSource {
    private readonly options;
    private readonly cache;
    constructor(options?: ConfigSourceOptions);
    /** A stable identifier for this loader instance (used by tooling and logs). */
    get id(): string;
    /** Merge all layers and return the resolved configuration object. */
    load(): Promise<ConfigObject>;
    /** Drop any cached result so the next load() re-reads all sources. */
    invalidate(): void;
}
/** Convenience wrapper matching the library's functional entry point. */
export declare function loadWithLoader(options?: ConfigSourceOptions, LoaderCtor?: new (options?: ConfigSourceOptions) => ConfigSource): Promise<ConfigObject>;
