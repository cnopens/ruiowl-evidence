"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.loadEnvLayer = loadEnvLayer;
const env_1 = require("../format/env");
/**
 * Build a config layer from environment variables that start with `prefix`.
 * `APP_PORT=8080` with prefix `APP` becomes `{ port: "8080" }`; nested keys
 * are created from `__` separators (e.g. APP_LOG__LEVEL -> log.level).
 */
function loadEnvLayer(prefix, env) {
    const out = {};
    const marker = `${prefix}_`;
    for (const [key, value] of Object.entries(env)) {
        if (!key.startsWith(marker) || value === undefined)
            continue;
        const path = key.slice(marker.length).toLowerCase().split("__");
        let cursor = out;
        for (let i = 0; i < path.length - 1; i++) {
            const part = path[i];
            const existing = cursor[part];
            if (typeof existing !== "object" || existing === null) {
                cursor[part] = {};
            }
            cursor = cursor[part];
        }
        cursor[path[path.length - 1]] = (0, env_1.parseEnvPairs)(value);
    }
    return out;
}
