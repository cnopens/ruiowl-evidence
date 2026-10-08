"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.logLoad = logLoad;
/** Emit a one-line debug message tagged with the loader's identity. */
function logLoad(loader, layerCount, tookMs) {
    const label = process.env.CONFIG_DEBUG === "1" ? console.debug : () => undefined;
    label(`[config] ${loader.id} merged ${layerCount} layer(s) in ${tookMs}ms`);
}
