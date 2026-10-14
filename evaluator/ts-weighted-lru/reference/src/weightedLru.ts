export type WeightedLRUOptions<K, V> = {
  maxWeight: number;
  weigh?: (value: V, key: K) => number;
  onEvict?: (key: K, value: V) => void;
};

export type WeightedLRUStats = { hits: number; misses: number; evictions: number };

type Entry<V> = { value: V; weight: number };

/** An LRU cache bounded by the total weight of its entries. */
export class WeightedLRU<K, V> {
  readonly maxWeight: number;
  #weigh: (value: V, key: K) => number;
  #onEvict: ((key: K, value: V) => void) | undefined;
  #entries = new Map<K, Entry<V>>();
  #totalWeight = 0;
  #hits = 0;
  #misses = 0;
  #evictions = 0;

  constructor(options: WeightedLRUOptions<K, V>) {
    const { maxWeight } = options;
    if (typeof maxWeight !== "number" || !Number.isFinite(maxWeight) || maxWeight <= 0) {
      throw new RangeError(`maxWeight must be a positive finite number, got ${maxWeight}`);
    }
    this.maxWeight = maxWeight;
    this.#weigh = options.weigh ?? (() => 1);
    this.#onEvict = options.onEvict;
  }

  get size(): number {
    return this.#entries.size;
  }

  get totalWeight(): number {
    return this.#totalWeight;
  }

  set(key: K, value: V): boolean {
    const weight = this.#weigh(value, key);
    if (typeof weight !== "number" || !Number.isFinite(weight) || weight < 0) {
      throw new RangeError(`invalid weight ${weight}`);
    }
    if (weight > this.maxWeight) {
      return false;
    }
    this.#remove(key);
    this.#entries.set(key, { value, weight });
    this.#totalWeight += weight;
    while (this.#totalWeight > this.maxWeight) {
      const [oldestKey, oldest] = this.#entries.entries().next().value as [K, Entry<V>];
      this.#remove(oldestKey);
      this.#evictions += 1;
      this.#onEvict?.(oldestKey, oldest.value);
    }
    return true;
  }

  get(key: K): V | undefined {
    const entry = this.#entries.get(key);
    if (entry === undefined) {
      this.#misses += 1;
      return undefined;
    }
    this.#hits += 1;
    this.#entries.delete(key);
    this.#entries.set(key, entry);
    return entry.value;
  }

  peek(key: K): V | undefined {
    return this.#entries.get(key)?.value;
  }

  has(key: K): boolean {
    return this.#entries.has(key);
  }

  delete(key: K): boolean {
    return this.#remove(key);
  }

  clear(): void {
    this.#entries.clear();
    this.#totalWeight = 0;
  }

  keys(): K[] {
    return [...this.#entries.keys()];
  }

  stats(): WeightedLRUStats {
    return { hits: this.#hits, misses: this.#misses, evictions: this.#evictions };
  }

  #remove(key: K): boolean {
    const entry = this.#entries.get(key);
    if (entry === undefined) {
      return false;
    }
    this.#entries.delete(key);
    this.#totalWeight -= entry.weight;
    return true;
  }
}
