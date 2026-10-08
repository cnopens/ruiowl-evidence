import type { ConfigObject } from "../types";
/**
 * Build a config layer from environment variables that start with `prefix`.
 * `APP_PORT=8080` with prefix `APP` becomes `{ port: "8080" }`; nested keys
 * are created from `__` separators (e.g. APP_LOG__LEVEL -> log.level).
 */
export declare function loadEnvLayer(prefix: string, env: NodeJS.ProcessEnv): ConfigObject;
