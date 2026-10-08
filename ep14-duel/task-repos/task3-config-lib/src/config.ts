import { ConfigLoader } from "./loader";
import type { ConfigLoaderOptions } from "./options";
import type { ConfigObject } from "./types";

/**
 * Functional entry point: create a {@link ConfigLoader} for `options` and
 * load the merged configuration.
 */
export async function loadConfig(options?: ConfigLoaderOptions): Promise<ConfigObject> {
  const loader = new ConfigLoader(options);
  return loader.load();
}
