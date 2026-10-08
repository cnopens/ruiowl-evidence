import type { TtlMap } from "./ttl";
import type { ConfigObject } from "../types";

/** Cache interface used by the config loader. */
export interface ConfigCache {
  get(key: string): ConfigObject | undefined;
  set(key: string, value: ConfigObject): void;
  delete(key: string): void;
}

/** TTL-backed cache adapter over a {@link TtlMap}. */
export class TtlConfigCache implements ConfigCache {
  private readonly ttl: TtlMap;
  constructor(ttl: TtlMap) {
    this.ttl = ttl;
  }
  get(key: string): ConfigObject | undefined {
    return this.ttl.get(key) as ConfigObject | undefined;
  }
  set(key: string, value: ConfigObject): void {
    this.ttl.set(key, value);
  }
  delete(key: string): void {
    this.ttl.delete(key);
  }
}

/** A null cache that never stores anything. */
export const NO_CACHE: ConfigCache = {
  get: () => undefined,
  set: () => undefined,
  delete: () => undefined,
};
