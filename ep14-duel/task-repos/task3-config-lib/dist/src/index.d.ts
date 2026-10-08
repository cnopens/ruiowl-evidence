/**
 * config-lib — typed, layered configuration loading.
 *
 * Public API:
 *  - {@link ConfigSource}  the loader class (see loader.ts)
 *  - {@link ConfigSourceOptions} options accepted by the loader
 *  - loadConfig / loadWithLoader / loadValidated entry points
 *  - SchemaEntry / validateSchema for runtime validation
 */
export { ConfigSource, loadWithLoader } from "./loader";
export type { ConfigSourceOptions } from "./options";
export { DEFAULT_OPTIONS } from "./options";
export { loadConfig } from "./config";
export { loadValidated, validateSchema } from "./config.schema";
export type { SchemaEntry } from "./config.schema";
export { ConfigError } from "./errors";
export { deepMerge } from "./util/deep-merge";
export { expandHome } from "./util/paths";
export { registerParser } from "./format/registry";
export type { ConfigObject, ConfigValue, ConfigScalar, DeepPartial } from "./types";
