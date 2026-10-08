/** A simple map with time-to-live expiry on read. */
export declare class TtlMap {
    private readonly store;
    private readonly ttlMs;
    constructor(ttlMs: number);
    get(key: string): unknown;
    set(key: string, value: unknown): void;
    delete(key: string): void;
}
