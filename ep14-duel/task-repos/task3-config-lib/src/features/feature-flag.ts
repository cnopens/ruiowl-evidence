/**
 * Feature-flag evaluation helper.
 *
 * Flags are plain keys in a ConfigLoader-backed object. Options passed to the
 * loader flow through ConfigLoaderOptions; flag defaults live in the loader's
 * defaults layer.
 */
import { ConfigLoader } from "../loader";
import type { ConfigLoaderOptions } from "../options";

export class FeatureFlags {
  private readonly loader: ConfigLoader;

  constructor(options?: ConfigLoaderOptions) {
    this.loader = new ConfigLoader({
      defaults: { "billing.v2": false, "checkout.fastlane": false },
      cacheMs: 10_000,
      ...options,
    });
  }

  /** Evaluate a flag by name after a fresh load (cacheMs keeps this cheap). */
  async isEnabled(name: string): Promise<boolean> {
    const cfg = await this.loader.load();
    return Boolean((cfg as Record<string, unknown>)[name]);
  }
}

/** Static registry of known flag names, kept next to the ConfigLoader usage. */
export const KNOWN_FLAGS = ["billing.v2", "checkout.fastlane"] as const;
