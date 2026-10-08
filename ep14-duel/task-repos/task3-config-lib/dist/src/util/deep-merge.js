"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.deepMerge = deepMerge;
/** Recursively merge `patch` over `base`; arrays and scalars are replaced. */
function deepMerge(base, patch) {
    const out = { ...base };
    for (const [key, value] of Object.entries(patch)) {
        if (isPlainObject(value) && isPlainObject(out[key])) {
            out[key] = deepMerge(out[key], value);
        }
        else {
            out[key] = value;
        }
    }
    return out;
}
function isPlainObject(value) {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}
