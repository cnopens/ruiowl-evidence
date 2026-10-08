import { describe, expect, it } from "vitest";
import { ConfigError } from "../src/errors";
import { ConfigLoader, loadConfig } from "../src";

describe("loadConfig", () => {
  it("merges defaults when no file or env sources are present", async () => {
    const cfg = await loadConfig({
      defaults: { port: 3000, log: { level: "info" } },
    });
    expect(cfg).toEqual({ port: 3000, log: { level: "info" } });
  });

  it("lets the environment layer override defaults", async () => {
    process.env.APP_PORT = "8080";
    process.env.APP_LOG__LEVEL = "debug";
    try {
      const cfg = await loadConfig({
        defaults: { port: 3000, log: { level: "info" } },
        envPrefix: "APP",
      });
      expect(cfg.port).toBe(8080);
      expect(cfg.log).toEqual({ level: "debug" });
    } finally {
      delete process.env.APP_PORT;
      delete process.env.APP_LOG__LEVEL;
    }
  });

  it("throws a ConfigError when a required key is missing", async () => {
    await expect(
      loadConfig({ defaults: { port: 1 }, required: ["db.host"] }),
    ).rejects.toBeInstanceOf(ConfigError);
  });

  it("returns the same object from cache until invalidate() is called", async () => {
    const loader = new ConfigLoader({ defaults: { port: 9999 }, cacheMs: 60_000 });
    const first = await loader.load();
    const second = await loader.load();
    expect(second).toBe(first); // served from cache

    loader.invalidate();
    const third = await loader.load();
    expect(third).toEqual({ port: 9999 });
    expect(third).not.toBe(first); // freshly merged
  });
});
