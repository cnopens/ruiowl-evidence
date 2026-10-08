"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConfigSource = void 0;
exports.loadWithLoader = loadWithLoader;
const config_cache_1 = require("./cache/config-cache");
const ttl_1 = require("./cache/ttl");
const file_source_1 = require("./source/file-source");
const env_source_1 = require("./source/env-source");
const defaults_source_1 = require("./source/defaults-source");
const options_1 = require("./options");
const validator_1 = require("./validate/validator");
const deep_merge_1 = require("./util/deep-merge");
/**
 * Loads configuration from layered sources with optional caching.
 *
 * Usage:
 * ```ts
 * const loader = new ConfigSource({ file: "./app.json", envPrefix: "APP" });
 * const cfg = await loader.load();
 * ```
 */
class ConfigSource {
    options;
    cache;
    constructor(options) {
        this.options = (0, options_1.resolveOptions)(options);
        this.cache = this.options.cacheMs > 0 ? new config_cache_1.TtlConfigCache(new ttl_1.TtlMap(this.options.cacheMs)) : config_cache_1.NO_CACHE;
    }
    /** A stable identifier for this loader instance (used by tooling and logs). */
    get id() {
        const file = this.options.file ?? "(defaults+env)";
        return `ConfigSource:${file}:${this.options.envPrefix ?? ""}`;
    }
    /** Merge all layers and return the resolved configuration object. */
    async load() {
        const cached = this.cache.get(this.id);
        if (cached !== undefined) {
            return cached;
        }
        const layers = [(0, defaults_source_1.defaultsLayer)(this.options.defaults)];
        if (this.options.file) {
            layers.push(await (0, file_source_1.loadFileLayer)(this.options.file));
        }
        if (this.options.envPrefix) {
            layers.push((0, env_source_1.loadEnvLayer)(this.options.envPrefix, process.env));
        }
        const merged = layers.reduce((acc, layer) => (0, deep_merge_1.deepMerge)(acc, layer), {});
        (0, validator_1.validateRequired)(merged, this.options.required);
        this.cache.set(this.id, merged);
        return merged;
    }
    /** Drop any cached result so the next load() re-reads all sources. */
    invalidate() {
        this.cache.delete(this.id);
    }
}
exports.ConfigSource = ConfigSource;
/** Convenience wrapper matching the library's functional entry point. */
async function loadWithLoader(options, LoaderCtor = ConfigSource) {
    const loader = new LoaderCtor(options);
    return loader.load();
}
