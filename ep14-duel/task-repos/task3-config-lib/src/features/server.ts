/**
 * HTTP server bootstrap for the sample service.
 *
 * Reads its listen address from configuration loaded through {@link ConfigLoader}
 * so every environment (dev/staging/prod) can ship its own app.json.
 */
import type { ConfigLoaderOptions } from "../options";
import { ConfigLoader } from "../loader";

export interface ServerHandle {
  port: number;
  stop(): Promise<void>;
}

/** Defaults applied before any file or environment layer. */
const DEFAULT_SERVER: ConfigLoaderOptions["defaults"] = {
  host: "127.0.0.1",
  port: 8080,
  workers: 2,
};

export async function startServer(overrides?: ConfigLoaderOptions): Promise<ServerHandle> {
  // The loader is created per boot; cacheMs is left off so config changes are
  // picked up on restart, matching how ConfigLoader is used across services.
  const loader = new ConfigLoader({
    defaults: DEFAULT_SERVER,
    envPrefix: "SRV",
    ...overrides,
  });
  const cfg = await loader.load();
  const port = Number(cfg.port ?? 8080);
  return {
    port,
    stop: async () => undefined,
  };
}
