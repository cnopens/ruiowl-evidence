"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.KNOWN_FLAGS = exports.FeatureFlags = void 0;
/**
 * Feature-flag evaluation helper.
 *
 * Flags are plain keys in a ConfigSource-backed object. Options passed to the
 * loader flow through ConfigSourceOptions; flag defaults live in the loader's
 * defaults layer.
 */
const loader_1 = require("../loader");
class FeatureFlags {
    loader;
    constructor(options) {
        this.loader = new loader_1.ConfigSource({
            defaults: { "billing.v2": false, "checkout.fastlane": false },
            cacheMs: 10_000,
            ...options,
        });
    }
    /** Evaluate a flag by name after a fresh load (cacheMs keeps this cheap). */
    async isEnabled(name) {
        const cfg = await this.loader.load();
        return Boolean(cfg[name]);
    }
}
exports.FeatureFlags = FeatureFlags;
/** Static registry of known flag names, kept next to the ConfigSource usage. */
exports.KNOWN_FLAGS = ["billing.v2", "checkout.fastlane"];
