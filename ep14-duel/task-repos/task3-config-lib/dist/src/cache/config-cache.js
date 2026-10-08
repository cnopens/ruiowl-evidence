"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.NO_CACHE = exports.TtlConfigCache = void 0;
/** TTL-backed cache adapter over a {@link TtlMap}. */
class TtlConfigCache {
    ttl;
    constructor(ttl) {
        this.ttl = ttl;
    }
    get(key) {
        return this.ttl.get(key);
    }
    set(key, value) {
        this.ttl.set(key, value);
    }
    delete(key) {
        this.ttl.delete(key);
    }
}
exports.TtlConfigCache = TtlConfigCache;
/** A null cache that never stores anything. */
exports.NO_CACHE = {
    get: () => undefined,
    set: () => undefined,
    delete: () => undefined,
};
