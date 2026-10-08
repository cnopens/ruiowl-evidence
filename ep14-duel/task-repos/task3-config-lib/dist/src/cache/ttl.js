"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TtlMap = void 0;
/** A simple map with time-to-live expiry on read. */
class TtlMap {
    store = new Map();
    ttlMs;
    constructor(ttlMs) {
        if (!Number.isFinite(ttlMs) || ttlMs <= 0) {
            throw new Error("TtlMap requires a positive ttlMs");
        }
        this.ttlMs = ttlMs;
    }
    get(key) {
        const item = this.store.get(key);
        if (!item)
            return undefined;
        if (Date.now() > item.expiresAt) {
            this.store.delete(key);
            return undefined;
        }
        return item.value;
    }
    set(key, value) {
        this.store.set(key, { expiresAt: Date.now() + this.ttlMs, value });
    }
    delete(key) {
        this.store.delete(key);
    }
}
exports.TtlMap = TtlMap;
