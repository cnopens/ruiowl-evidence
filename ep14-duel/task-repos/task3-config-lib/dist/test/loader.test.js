"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const vitest_1 = require("vitest");
const errors_1 = require("../src/errors");
const src_1 = require("../src");
(0, vitest_1.describe)("loadConfig", () => {
    (0, vitest_1.it)("merges defaults when no file or env sources are present", async () => {
        const cfg = await (0, src_1.loadConfig)({
            defaults: { port: 3000, log: { level: "info" } },
        });
        (0, vitest_1.expect)(cfg).toEqual({ port: 3000, log: { level: "info" } });
    });
    (0, vitest_1.it)("lets the environment layer override defaults", async () => {
        process.env.APP_PORT = "8080";
        process.env.APP_LOG__LEVEL = "debug";
        try {
            const cfg = await (0, src_1.loadConfig)({
                defaults: { port: 3000, log: { level: "info" } },
                envPrefix: "APP",
            });
            (0, vitest_1.expect)(cfg.port).toBe(8080);
            (0, vitest_1.expect)(cfg.log).toEqual({ level: "debug" });
        }
        finally {
            delete process.env.APP_PORT;
            delete process.env.APP_LOG__LEVEL;
        }
    });
    (0, vitest_1.it)("throws a ConfigError when a required key is missing", async () => {
        await (0, vitest_1.expect)((0, src_1.loadConfig)({ defaults: { port: 1 }, required: ["db.host"] })).rejects.toBeInstanceOf(errors_1.ConfigError);
    });
    (0, vitest_1.it)("returns the same object from cache until invalidate() is called", async () => {
        const loader = new src_1.ConfigSource({ defaults: { port: 9999 }, cacheMs: 60_000 });
        const first = await loader.load();
        const second = await loader.load();
        (0, vitest_1.expect)(second).toBe(first); // served from cache
        loader.invalidate();
        const third = await loader.load();
        (0, vitest_1.expect)(third).toEqual({ port: 9999 });
        (0, vitest_1.expect)(third).not.toBe(first); // freshly merged
    });
});
