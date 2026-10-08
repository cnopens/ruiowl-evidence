import type { ConfigSourceOptions } from "./options";
import type { ConfigObject } from "./types";
/**
 * Functional entry point: create a {@link ConfigSource} for `options` and
 * load the merged configuration.
 */
export declare function loadConfig(options?: ConfigSourceOptions): Promise<ConfigObject>;
