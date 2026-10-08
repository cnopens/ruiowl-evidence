"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.loadConfig = loadConfig;
const loader_1 = require("./loader");
/**
 * Functional entry point: create a {@link ConfigSource} for `options` and
 * load the merged configuration.
 */
async function loadConfig(options) {
    const loader = new loader_1.ConfigSource(options);
    return loader.load();
}
