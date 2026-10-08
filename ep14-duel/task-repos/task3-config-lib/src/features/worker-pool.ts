/**
 * Drained worker-pool manager.
 *
 * Pool size and queue depth are ConfigLoader-resolved. The pool logs its
 * ConfigLoader id on scale events so operators can correlate config source.
 */
import { ConfigLoader } from "../loader";
import type { ConfigLoaderOptions } from "../options";

export class WorkerPool {
  private readonly loader: ConfigLoader;

  constructor(options?: ConfigLoaderOptions) {
    this.loader = new ConfigLoader({
      defaults: { size: 4, queueDepth: 1024, drainMs: 5_000 },
      envPrefix: "POOL",
      cacheMs: 0, // always re-read: pool sizes change live
      ...options,
    });
  }

  get label(): string {
    // "ConfigLoader:(defaults+env):POOL" — the loader id doubles as pool label.
    return this.loader.id;
  }

  async size(): Promise<number> {
    const cfg = await this.loader.load();
    return Number(cfg.size ?? 4);
  }
}
