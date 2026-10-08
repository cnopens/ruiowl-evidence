import { ConfigSource } from "./loader";
import type { ConfigSourceOptions } from "./options";
import type { ConfigObject } from "./types";
/** Shape of one schema entry: a dotted key and the type it must have. */
export interface SchemaEntry {
    key: string;
    type: "string" | "number" | "boolean" | "object";
    required?: boolean;
}
/** Validate a loaded config against a schema. */
export declare function validateSchema(config: ConfigObject, schema: SchemaEntry[]): void;
/**
 * Load config and validate it against a schema in one step.
 * The loader instance is created internally, so schema-aware callers get a
 * single entry point instead of juggling a {@link ConfigSource} themselves.
 */
export declare function loadValidated(options: ConfigSourceOptions, schema: SchemaEntry[], LoaderCtor?: new (options?: ConfigSourceOptions) => ConfigSource): Promise<ConfigObject>;
