import { ConfigLoader } from "./loader";
import type { ConfigLoaderOptions } from "./options";
import type { ConfigObject } from "./types";

/** Shape of one schema entry: a dotted key and the type it must have. */
export interface SchemaEntry {
  key: string;
  type: "string" | "number" | "boolean" | "object";
  required?: boolean;
}

/** Validate a loaded config against a schema. */
export function validateSchema(config: ConfigObject, schema: SchemaEntry[]): void {
  for (const entry of schema) {
    const parts = entry.key.split(".");
    let cursor: unknown = config;
    let missing = false;
    for (const part of parts) {
      if (typeof cursor !== "object" || cursor === null || !(part in (cursor as object))) {
        missing = true;
        break;
      }
      cursor = (cursor as Record<string, unknown>)[part];
    }
    if (missing) {
      if (entry.required) {
        throw new Error(`config key ${entry.key} is required but missing`);
      }
      continue;
    }
    const actual = typeof cursor;
    if (entry.type === "object") {
      if (typeof cursor !== "object" || cursor === null || Array.isArray(cursor)) {
        throw new Error(`config key ${entry.key} must be an object, got ${actual}`);
      }
    } else if (actual !== entry.type) {
      throw new Error(`config key ${entry.key} must be ${entry.type}, got ${actual}`);
    }
  }
}

/**
 * Load config and validate it against a schema in one step.
 * The loader instance is created internally, so schema-aware callers get a
 * single entry point instead of juggling a {@link ConfigLoader} themselves.
 */
export async function loadValidated(
  options: ConfigLoaderOptions,
  schema: SchemaEntry[],
  LoaderCtor: new (options?: ConfigLoaderOptions) => ConfigLoader = ConfigLoader,
): Promise<ConfigObject> {
  const loader = new LoaderCtor(options);
  const config = await loader.load();
  validateSchema(config, schema);
  return config;
}
