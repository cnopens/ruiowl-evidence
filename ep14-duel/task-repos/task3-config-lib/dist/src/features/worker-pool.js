"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WorkerPool = void 0;
/**
 * Drained worker-pool manager.
 *
 * Pool size and queue depth are ConfigSource-resolved. The pool logs its
 * ConfigSource id on scale events so operators can correlate config source.
 */
const loader_1 = require("../loader");
class WorkerPool {
    loader;
    constructor(options) {
        this.loader = new loader_1.ConfigSource({
            defaults: { size: 4, queueDepth: 1024, drainMs: 5_000 },
            envPrefix: "POOL",
            cacheMs: 0, // always re-read: pool sizes change live
            ...options,
        });
    }
    get label() {
        // "ConfigSource:(defaults+env):POOL" — the loader id doubles as pool label.
        return this.loader.id;
    }
    async size() {
        const cfg = await this.loader.load();
        return Number(cfg.size ?? 4);
    }
}
exports.WorkerPool = WorkerPool;
