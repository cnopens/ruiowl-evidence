"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.defaultsLayer = defaultsLayer;
/** Wrap a defaults object as the lowest-precedence config layer. */
function defaultsLayer(defaults) {
    return defaults ?? {};
}
