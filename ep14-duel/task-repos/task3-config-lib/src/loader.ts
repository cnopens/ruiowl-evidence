import { NO_CACHE, TtlConfigCache } from "./cache/config-cache";
import { TtlMap } from "./cache/ttl";
import { ConfigError } from "./errors";
import { loadFileLayer } from "./source/file-source";
import { loadEnvLayer } from "./source/env-source";
import { defaultsLayer } from "./source/defaults-source";
import { ConfigLoaderOptions, resolveOptions } from "./options";
import { validateRequired } from "./validate/validator";
import { deepMerge } from "./util/deep-merge";
import type { ConfigObject } from "./types";

/**
 * Loads configuration from layered sources with optional caching.
 *
 * Usage:
 * ```ts
 * const loader = new ConfigLoader({ file: "./app.json", envPrefix: "APP" });
 * const cfg = await loader.load();
 * ```
 */
export class ConfigLoader {
  private readonly options: Required<ConfigLoaderOptions>;
  private readonly cache: TtlConfigCache | typeof NO_CACHE;

  constructor(options?: ConfigLoaderOptions) {
    this.options = resolveOptions(options);
    this.cache = this.options.cacheMs > 0 ? new TtlConfigCache(new TtlMap(this.options.cacheMs)) : NO_CACHE;
  }

  /** A stable identifier for this loader instance (used by tooling and logs). */
  get id(): string {
    const file = this.options.file ?? "(defaults+env)";
    return `ConfigLoader:${file}:${this.options.envPrefix ?? ""}`;
  }

  /** Merge all layers and return the resolved configuration object. */
  async load(): Promise<ConfigObject> {
    const cached = this.cache.get(this.id);
    if (cached !== undefined) {
      return cached;
    }

    const layers: ConfigObject[] = [defaultsLayer(this.options.defaults)];

    if (this.options.file) {
      layers.push(await loadFileLayer(this.options.file));
    }
    if (this.options.envPrefix) {
      layers.push(loadEnvLayer(this.options.envPrefix, process.env));
    }

    const merged = layers.reduce<ConfigObject>((acc, layer) => deepMerge(acc, layer), {});
    validateRequired(merged, this.options.required);

    this.cache.set(this.id, merged);
    return merged;
  }

  /** Drop any cached result so the next load() re-reads all sources. */
  invalidate(): void {
    this.cache.delete(this.id);
  }
}

/** Convenience wrapper matching the library's functional entry point. */
export async function loadWithLoader(
  options?: ConfigLoaderOptions,
  LoaderCtor: new (options?: ConfigLoaderOptions) => ConfigLoader = ConfigLoader,
): Promise<ConfigObject> {
  const loader = new LoaderCtor(options);
  return loader.load();
}
