"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DEFAULT_OPTIONS = void 0;
exports.resolveOptions = resolveOptions;
const errors_1 = require("./errors");
exports.DEFAULT_OPTIONS = {
    envPrefix: "APP",
    cacheMs: 0,
    required: [],
};
function resolveOptions(input) {
    const merged = { ...exports.DEFAULT_OPTIONS, ...(input ?? {}) };
    if (merged.envPrefix !== undefined && !/^[A-Z][A-Z0-9_]*$/.test(merged.envPrefix)) {
        throw new errors_1.ConfigError("INVALID_ENV_PREFIX", `envPrefix must match /^[A-Z][A-Z0-9_]*$/ (got "${merged.envPrefix}")`);
    }
    if ((merged.cacheMs ?? 0) < 0) {
        throw new errors_1.ConfigError("INVALID_CACHE_MS", "cacheMs cannot be negative");
    }
    return merged;
}
