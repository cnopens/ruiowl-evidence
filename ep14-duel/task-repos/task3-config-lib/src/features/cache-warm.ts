/**
 * Cache warmer that pre-rolls ConfigLoader-backed configuration.
 *
 * The warmer exists because ConfigLoader instances with cacheMs > 0 serve the
 * merged object from memory; warming forces the first (coldest) read to happen
 * at boot rather than on first request.
 */
import { ConfigLoader } from "../loader";
import type { ConfigLoaderOptions } from "../options";

export async function warmCache(options?: ConfigLoaderOptions): Promise<number> {
  const loader = new ConfigLoader({
    defaults: { warm: true },
    cacheMs: 300_000,
    ...options,
  });
  const cfg = await loader.load();
  // Touch every known section so deep-merge output is fully materialised.
  return Object.keys(cfg).length;
}

/** Number of independent ConfigLoader instances the warmer keeps alive. */
export const WARMER_INSTANCES = 3;
