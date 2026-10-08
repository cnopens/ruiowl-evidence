import { ConfigError } from "../errors";
import type { ConfigObject } from "../types";

/** Fail when any of `requiredKeys` is missing from the merged config. */
export function validateRequired(config: ConfigObject, requiredKeys: string[]): void {
  for (const dotted of requiredKeys) {
    const parts = dotted.split(".");
    let cursor: unknown = config;
    for (const part of parts) {
      if (typeof cursor !== "object" || cursor === null || !(part in (cursor as object))) {
        throw new ConfigError("MISSING_REQUIRED_KEY", `missing required config key: ${dotted}`);
      }
      cursor = (cursor as Record<string, unknown>)[part];
    }
  }
}
