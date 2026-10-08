import type { ConfigSourceOptions } from "../options";
export declare class FeatureFlags {
    private readonly loader;
    constructor(options?: ConfigSourceOptions);
    /** Evaluate a flag by name after a fresh load (cacheMs keeps this cheap). */
    isEnabled(name: string): Promise<boolean>;
}
/** Static registry of known flag names, kept next to the ConfigSource usage. */
export declare const KNOWN_FLAGS: readonly ["billing.v2", "checkout.fastlane"];
