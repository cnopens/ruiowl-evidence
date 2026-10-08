"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.parseEnvPairs = parseEnvPairs;
/** Coerce a single environment value into a scalar (number/bool passthrough). */
function parseEnvPairs(value) {
    if (value === "true")
        return true;
    if (value === "false")
        return false;
    if (/^-?\d+$/.test(value)) {
        const n = Number(value);
        if (Number.isSafeInteger(n))
            return n;
    }
    return value;
}
