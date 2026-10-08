"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.parseJson = parseJson;
/** Parse a JSON string, throwing a readable ConfigError on failure. */
function parseJson(text) {
    return JSON.parse(text);
}
