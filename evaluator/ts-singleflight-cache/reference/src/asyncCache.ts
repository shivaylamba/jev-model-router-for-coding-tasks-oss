export type AsyncCacheOptions<V> = {
  load: (key: string) => Promise<V>;
  ttlMs: number;
  staleMs: number;
  maxEntries: number;
  now?: () => number;
  onRefreshError?: (key: string, error: unknown) => void;
};

type Entry<V> = { value: V; storedAt: number };
type Flight<V> = { promise: Promise<V>; generation: number };

/** TTL + stale-while-revalidate + single-flight + LRU. See docs/ASYNC_CACHE.md. */
export class AsyncCache<V> {
  #load: (key: string) => Promise<V>;
  #ttlMs: number;
  #staleMs: number;
  #maxEntries: number;
  #now: () => number;
  #onRefreshError: ((key: string, error: unknown) => void) | undefined;
  // Map order is recency order: first = least recently used.
  #entries = new Map<string, Entry<V>>();
  #flights = new Map<string, Flight<V>>();
  // Bumped per key on invalidate (and globally on clear) so stale loads do not store.
  #generations = new Map<string, number>();
  #epoch = 0;

  constructor(options: AsyncCacheOptions<V>) {
    const { ttlMs, staleMs, maxEntries } = options;
    if (typeof ttlMs !== "number" || !Number.isFinite(ttlMs) || ttlMs <= 0) {
      throw new RangeError(`ttlMs must be a positive finite number, got ${ttlMs}`);
    }
    if (typeof staleMs !== "number" || !Number.isFinite(staleMs) || staleMs < 0) {
      throw new RangeError(`staleMs must be a finite number >= 0, got ${staleMs}`);
    }
    if (!Number.isInteger(maxEntries) || maxEntries < 1) {
      throw new RangeError(`maxEntries must be an integer >= 1, got ${maxEntries}`);
    }
    this.#load = options.load;
    this.#ttlMs = ttlMs;
    this.#staleMs = staleMs;
    this.#maxEntries = maxEntries;
    this.#now = options.now ?? Date.now;
    this.#onRefreshError = options.onRefreshError;
  }

  get size(): number {
    const now = this.#now();
    let count = 0;
    for (const entry of this.#entries.values()) {
      if (this.#state(entry, now) !== "expired") count += 1;
    }
    return count;
  }

  get(key: string): Promise<V> {
    const entry = this.#entries.get(key);
    if (entry !== undefined) {
      const state = this.#state(entry, this.#now());
      if (state !== "expired") {
        this.#touch(key, entry);
        if (state === "stale" && !this.#flights.has(key)) {
          this.#start(key).promise.catch((error) => {
            this.#onRefreshError?.(key, error);
          });
        }
        return Promise.resolve(entry.value);
      }
      this.#entries.delete(key);
    }
    const flight = this.#flights.get(key) ?? this.#start(key);
    return flight.promise;
  }

  peek(key: string): V | undefined {
    const entry = this.#entries.get(key);
    if (entry === undefined || this.#state(entry, this.#now()) === "expired") {
      return undefined;
    }
    return entry.value;
  }

  invalidate(key: string): boolean {
    this.#generations.set(key, this.#generation(key) + 1);
    this.#flights.delete(key);
    return this.#entries.delete(key);
  }

  clear(): void {
    this.#epoch += 1;
    this.#generations.clear();
    this.#flights.clear();
    this.#entries.clear();
  }

  #generation(key: string): number {
    return this.#generations.get(key) ?? 0;
  }

  #token(key: string): number {
    // Combines the global epoch and the per-key generation into one comparable number.
    return this.#epoch * 1_000_000_007 + this.#generation(key);
  }

  #start(key: string): Flight<V> {
    const token = this.#token(key);
    let promise: Promise<V>;
    try {
      promise = Promise.resolve(this.#load(key));
    } catch (error) {
      promise = Promise.reject(error);
    }
    const flight: Flight<V> = {
      generation: token,
      promise: promise.then(
        (value) => {
          if (this.#flights.get(key) === flight) this.#flights.delete(key);
          if (this.#token(key) === token) this.#store(key, value);
          return value;
        },
        (error) => {
          if (this.#flights.get(key) === flight) this.#flights.delete(key);
          throw error;
        },
      ),
    };
    this.#flights.set(key, flight);
    return flight;
  }

  #store(key: string, value: V): void {
    this.#entries.delete(key);
    this.#entries.set(key, { value, storedAt: this.#now() });
    if (this.#entries.size <= this.#maxEntries) return;
    const now = this.#now();
    for (const [k, entry] of this.#entries) {
      if (this.#state(entry, now) === "expired") this.#entries.delete(k);
    }
    while (this.#entries.size > this.#maxEntries) {
      const oldest = this.#entries.keys().next().value as string;
      this.#entries.delete(oldest);
    }
  }

  #touch(key: string, entry: Entry<V>): void {
    this.#entries.delete(key);
    this.#entries.set(key, entry);
  }

  #state(entry: Entry<V>, now: number): "fresh" | "stale" | "expired" {
    const age = now - entry.storedAt;
    if (age < this.#ttlMs) return "fresh";
    if (age < this.#ttlMs + this.#staleMs) return "stale";
    return "expired";
  }
}
