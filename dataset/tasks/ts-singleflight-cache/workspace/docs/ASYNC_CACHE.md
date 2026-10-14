# AsyncCache

A cache for slow asynchronous lookups, in `src/asyncCache.ts`. It combines a
time-to-live, stale-while-revalidate, request coalescing ("single flight") and
a least-recently-used size limit. Time comes from an injected clock so it can
be tested without waiting.

## API

```ts
export type AsyncCacheOptions<V> = {
  load: (key: string) => Promise<V>;
  ttlMs: number;      // finite, > 0
  staleMs: number;    // finite, >= 0
  maxEntries: number; // integer, >= 1
  now?: () => number; // current time in ms; defaults to Date.now
  onRefreshError?: (key: string, error: unknown) => void;
};

export class AsyncCache<V> {
  constructor(options: AsyncCacheOptions<V>);
  get(key: string): Promise<V>;
  peek(key: string): V | undefined;
  invalidate(key: string): boolean;
  clear(): void;
  get size(): number;
}
```

The constructor throws `RangeError` if `ttlMs`, `staleMs` or `maxEntries` break
the constraints above.

## Entry age

A stored value remembers `storedAt`, the `now()` reading taken **when its load
settled** (not when the load started). Its age is `now() - storedAt`:

- **fresh** while `age < ttlMs`;
- **stale** while `ttlMs <= age < ttlMs + staleMs`;
- **expired** once `age >= ttlMs + staleMs`. An expired value is never returned.

## Loads

A load is one call to `options.load(key)`. There is **at most one load in
flight per key**. If `load` throws synchronously, that is treated exactly like
a load that returned a rejected promise (`get` never throws synchronously).

When a load fulfils, its value is stored for the key with `storedAt = now()`,
as the most recently used entry, replacing any previous value. The exception:
if the key was invalidated, or the cache cleared, after that load started, the
value is **not** stored (callers waiting on that load still receive it).

When a load rejects, nothing is stored and any value already stored for the
key is left as it is.

When a load settles, the key no longer has a load in flight (unless a newer
load for the key has been started since, which is unaffected).

## get(key)

1. **Fresh value:** resolve with it; the entry becomes most recently used. No
   load is started.
2. **Stale value:** resolve with the stale value right away; the entry becomes
   most recently used. If no load is in flight for the key, start one in the
   background (a *refresh*). If a refresh rejects, the error is passed to
   `onRefreshError(key, error)` when that option is given and is otherwise
   ignored (it must never surface as an unhandled rejection). The stale value
   keeps being served until it expires, and each later `get` that finds it
   stale with no load in flight starts another refresh.
3. **No value, or an expired one:** the expired value (if any) is dropped. If a
   load is in flight for the key (an earlier `get` or a refresh), return a
   promise that settles the same way as that load. Otherwise start a load and
   return a promise that settles the same way as it. A rejected load rejects
   every `get` waiting on it with the same error; `onRefreshError` is only
   called for loads that were started as refreshes.

## peek(key)

Returns the value if it is fresh or stale, otherwise `undefined`. It never
starts a load and does not change recency.

## invalidate(key) and clear()

`invalidate(key)` removes the stored value for the key and returns `true` if
there was one (in any state), otherwise `false`. A load already in flight for
the key will not store its result, and the next `get` for the key starts a new
load instead of waiting on that one.

`clear()` does the same for every key.

## Size limit

`size` is the number of stored values that are fresh or stale at `now()`.

Whenever storing a value leaves more than `maxEntries` values stored, the cache
first drops every expired value, then, while still over the limit, evicts the
least recently used values. An entry becomes "used" when it is stored and when
`get` returns it (fresh or stale). Loads in flight do not count towards the
limit, and evicting a key does not stop its in-flight load from storing its
result later.
