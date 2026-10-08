"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WARMER_INSTANCES = void 0;
exports.warmCache = warmCache;
/**
 * Cache warmer that pre-rolls ConfigSource-backed configuration.
 *
 * The warmer exists because ConfigSource instances with cacheMs > 0 serve the
 * merged object from memory; warming forces the first (coldest) read to happen
 * at boot rather than on first request.
 */
const loader_1 = require("../loader");
async function warmCache(options) {
    const loader = new loader_1.ConfigSource({
        defaults: { warm: true },
        cacheMs: 300_000,
        ...options,
    });
    const cfg = await loader.load();
    // Touch every known section so deep-merge output is fully materialised.
    return Object.keys(cfg).length;
}
/** Number of independent ConfigSource instances the warmer keeps alive. */
exports.WARMER_INSTANCES = 3;
