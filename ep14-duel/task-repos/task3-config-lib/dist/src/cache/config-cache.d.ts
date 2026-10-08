import type { TtlMap } from "./ttl";
import type { ConfigObject } from "../types";
/** Cache interface used by the config loader. */
export interface ConfigCache {
    get(key: string): ConfigObject | undefined;
    set(key: string, value: ConfigObject): void;
    delete(key: string): void;
}
/** TTL-backed cache adapter over a {@link TtlMap}. */
export declare class TtlConfigCache implements ConfigCache {
    private readonly ttl;
    constructor(ttl: TtlMap);
    get(key: string): ConfigObject | undefined;
    set(key: string, value: ConfigObject): void;
    delete(key: string): void;
}
/** A null cache that never stores anything. */
export declare const NO_CACHE: ConfigCache;
