"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.createApiClient = createApiClient;
/**
 * API client factory.
 *
 * Shows ConfigSourceOptions being passed through a functional entry point
 * (loadWithLoader) rather than constructing a ConfigSource directly.
 */
const loader_1 = require("../loader");
const DEFAULTS = {
    baseUrl: "https://api.example.test",
    timeoutMs: 3000,
    retries: 2,
};
/**
 * Create a configured API client. `options` are ConfigSourceOptions; the
 * loader is constructed inside loadWithLoader so callers never touch the
 * ConfigSource class directly.
 */
async function createApiClient(options) {
    const cfg = await (0, loader_1.loadWithLoader)({
        defaults: DEFAULTS,
        envPrefix: "API",
        ...options,
    });
    return {
        baseUrl: String(cfg.baseUrl),
        timeoutMs: Number(cfg.timeoutMs),
        retries: Number(cfg.retries),
    };
}
