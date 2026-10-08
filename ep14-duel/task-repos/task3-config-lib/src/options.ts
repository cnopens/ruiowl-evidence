import { ConfigError } from "./errors";
import type { ConfigObject } from "./types";

/**
 * Options accepted by {@link ConfigLoader}.
 *
 * Layers are merged in order of increasing precedence:
 * defaults < file < environment.
 */
export interface ConfigLoaderOptions {
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

export const DEFAULT_OPTIONS: Readonly<ConfigLoaderOptions> = {
  envPrefix: "APP",
  cacheMs: 0,
  required: [],
};

export function resolveOptions(input: ConfigLoaderOptions | undefined): Required<ConfigLoaderOptions> {
  const merged: ConfigLoaderOptions = { ...DEFAULT_OPTIONS, ...(input ?? {}) };
  if (merged.envPrefix !== undefined && !/^[A-Z][A-Z0-9_]*$/.test(merged.envPrefix)) {
    throw new ConfigError(
      "INVALID_ENV_PREFIX",
      `envPrefix must match /^[A-Z][A-Z0-9_]*$/ (got "${merged.envPrefix}")`,
    );
  }
  if ((merged.cacheMs ?? 0) < 0) {
    throw new ConfigError("INVALID_CACHE_MS", "cacheMs cannot be negative");
  }
  return merged as Required<ConfigLoaderOptions>;
}
