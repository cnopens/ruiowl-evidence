/**
 * API client factory.
 *
 * Shows ConfigLoaderOptions being passed through a functional entry point
 * (loadWithLoader) rather than constructing a ConfigLoader directly.
 */
import { loadWithLoader } from "../loader";
import type { ConfigLoaderOptions } from "../options";
import type { ConfigObject } from "../types";

export interface ApiClientConfig {
  baseUrl: string;
  timeoutMs: number;
  retries: number;
}

const DEFAULTS: ConfigObject = {
  baseUrl: "https://api.example.test",
  timeoutMs: 3000,
  retries: 2,
};

/**
 * Create a configured API client. `options` are ConfigLoaderOptions; the
 * loader is constructed inside loadWithLoader so callers never touch the
 * ConfigLoader class directly.
 */
export async function createApiClient(options?: ConfigLoaderOptions): Promise<ApiClientConfig> {
  const cfg = await loadWithLoader({
    defaults: DEFAULTS,
    envPrefix: "API",
    ...options,
  });
  return {
    baseUrl: String(cfg.baseUrl),
    timeoutMs: Number(cfg.timeoutMs),
    retries: Number(cfg.retries),
  };
}
