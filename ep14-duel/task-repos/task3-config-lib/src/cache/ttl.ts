/** A simple map with time-to-live expiry on read. */
export class TtlMap {
  private readonly store = new Map<string, { expiresAt: number; value: unknown }>();
  private readonly ttlMs: number;

  constructor(ttlMs: number) {
    if (!Number.isFinite(ttlMs) || ttlMs <= 0) {
      throw new Error("TtlMap requires a positive ttlMs");
    }
    this.ttlMs = ttlMs;
  }

  get(key: string): unknown {
    const item = this.store.get(key);
    if (!item) return undefined;
    if (Date.now() > item.expiresAt) {
      this.store.delete(key);
      return undefined;
    }
    return item.value;
  }

  set(key: string, value: unknown): void {
    this.store.set(key, { expiresAt: Date.now() + this.ttlMs, value });
  }

  delete(key: string): void {
    this.store.delete(key);
  }
}
