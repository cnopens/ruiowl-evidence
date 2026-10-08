import type { ConfigObject, ConfigValue } from "../types";

/** Recursively merge `patch` over `base`; arrays and scalars are replaced. */
export function deepMerge(base: ConfigObject, patch: ConfigObject): ConfigObject {
  const out: Record<string, unknown> = { ...base };
  for (const [key, value] of Object.entries(patch)) {
    if (isPlainObject(value) && isPlainObject(out[key])) {
      out[key] = deepMerge(out[key] as ConfigObject, value as ConfigObject);
    } else {
      out[key] = value;
    }
  }
  return out as ConfigObject;
}

function isPlainObject(value: ConfigValue | unknown): value is ConfigObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
