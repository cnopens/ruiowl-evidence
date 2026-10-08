/**
 * HTTP server bootstrap for the sample service.
 *
 * Reads its listen address from configuration loaded through {@link ConfigSource}
 * so every environment (dev/staging/prod) can ship its own app.json.
 */
import type { ConfigSourceOptions } from "../options";
export interface ServerHandle {
    port: number;
    stop(): Promise<void>;
}
export declare function startServer(overrides?: ConfigSourceOptions): Promise<ServerHandle>;
