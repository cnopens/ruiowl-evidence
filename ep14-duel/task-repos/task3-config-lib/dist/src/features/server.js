"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.startServer = startServer;
const loader_1 = require("../loader");
/** Defaults applied before any file or environment layer. */
const DEFAULT_SERVER = {
    host: "127.0.0.1",
    port: 8080,
    workers: 2,
};
async function startServer(overrides) {
    // The loader is created per boot; cacheMs is left off so config changes are
    // picked up on restart, matching how ConfigSource is used across services.
    const loader = new loader_1.ConfigSource({
        defaults: DEFAULT_SERVER,
        envPrefix: "SRV",
        ...overrides,
    });
    const cfg = await loader.load();
    const port = Number(cfg.port ?? 8080);
    return {
        port,
        stop: async () => undefined,
    };
}
