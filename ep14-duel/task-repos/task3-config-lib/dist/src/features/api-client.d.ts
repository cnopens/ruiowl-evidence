import type { ConfigSourceOptions } from "../options";
export interface ApiClientConfig {
    baseUrl: string;
    timeoutMs: number;
    retries: number;
}
/**
 * Create a configured API client. `options` are ConfigSourceOptions; the
 * loader is constructed inside loadWithLoader so callers never touch the
 * ConfigSource class directly.
 */
export declare function createApiClient(options?: ConfigSourceOptions): Promise<ApiClientConfig>;
