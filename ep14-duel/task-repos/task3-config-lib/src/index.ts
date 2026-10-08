/**
 * config-lib — typed, layered configuration loading.
 *
 * Public API:
 *  - {@link ConfigLoader}  the loader class (see loader.ts)
 *  - {@link ConfigLoaderOptions} options accepted by the loader
 *  - loadConfig / loadWithLoader / loadValidated entry points
 *  - SchemaEntry / validateSchema for runtime validation
 */

export { ConfigLoader, loadWithLoader } from "./loader";
export type { ConfigLoaderOptions } from "./options";
export { DEFAULT_OPTIONS } from "./options";
export { loadConfig } from "./config";
export { loadValidated, validateSchema } from "./config.schema";
export type { SchemaEntry } from "./config.schema";
export { ConfigError } from "./errors";
export { deepMerge } from "./util/deep-merge";
export { expandHome } from "./util/paths";
export { registerParser } from "./format/registry";
export type { ConfigObject, ConfigValue, ConfigScalar, DeepPartial } from "./types";
