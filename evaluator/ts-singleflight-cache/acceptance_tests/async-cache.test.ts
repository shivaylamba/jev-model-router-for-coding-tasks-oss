import { test } from "node:test";
import assert from "node:assert/strict";
import { AsyncCache, type AsyncCacheOptions } from "../src/asyncCache.ts";

type Deferred<T> = { promise: Promise<T>; resolve: (value: T) => void; reject: (error: unknown) => void };

function deferred<T>(): Deferred<T> {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

/** Let pending promise callbacks run. No real time passes. */
const flush = () => new Promise<void>((resolve) => setImmediate(resolve));

/** A load function whose calls the test settles by hand. */
function harness(options: Partial<AsyncCacheOptions<string>> = {}) {
  const clock = { t: 0 };
  const calls: Array<{ key: string; d: Deferred<string> }> = [];
  const refreshErrors: Array<[string, unknown]> = [];
  const cache = new AsyncCache<string>({
    load: (key) => {
      const d = deferred<string>();
      calls.push({ key, d });
      return d.promise;
    },
    ttlMs: 1000,
    staleMs: 500,
    maxEntries: 10,
    now: () => clock.t,
    onRefreshError: (key, error) => refreshErrors.push([key, error]),
    ...options,
  });
  return { cache, clock, calls, refreshErrors };
}

/** Track whether a promise has settled yet. */
function track<T>(promise: Promise<T>) {
  const state = { settled: false, value: undefined as T | undefined, error: undefined as unknown };
  promise.then(
    (value) => { state.settled = true; state.value = value; },
    (error) => { state.settled = true; state.error = error; },
  );
  return state;
}

async function loaded(h: ReturnType<typeof harness>, key: string, value: string) {
  const pending = h.cache.get(key);
  h.calls.at(-1)!.d.resolve(value);
  assert.equal(await pending, value);
}

test("invalid options throw RangeError", () => {
  const load = async () => "x";
  for (const bad of [
    { ttlMs: 0, staleMs: 0, maxEntries: 1 },
    { ttlMs: Number.POSITIVE_INFINITY, staleMs: 0, maxEntries: 1 },
    { ttlMs: 10, staleMs: -1, maxEntries: 1 },
    { ttlMs: 10, staleMs: 0, maxEntries: 0 },
    { ttlMs: 10, staleMs: 0, maxEntries: 1.5 },
  ]) {
    assert.throws(() => new AsyncCache({ load, ...bad }), RangeError);
  }
});

test("a fresh value is served without loading again", async () => {
  const h = harness();
  await loaded(h, "a", "A1");
  h.clock.t = 999;
  assert.equal(await h.cache.get("a"), "A1");
  assert.equal(h.calls.length, 1);
  assert.equal(h.cache.peek("a"), "A1");
});

test("concurrent gets for one key share a single load", async () => {
  const h = harness();
  const first = h.cache.get("a");
  const second = h.cache.get("a");
  const other = h.cache.get("b");
  assert.deepEqual(h.calls.map((c) => c.key), ["a", "b"]);
  h.calls[0].d.resolve("A1");
  h.calls[1].d.resolve("B1");
  assert.deepEqual(await Promise.all([first, second, other]), ["A1", "A1", "B1"]);
});

test("age is measured from when the load settled", async () => {
  const h = harness();
  const pending = h.cache.get("a");
  h.clock.t = 400;
  h.calls[0].d.resolve("A1");
  await pending;
  h.clock.t = 1399;
  assert.equal(await h.cache.get("a"), "A1");
  assert.equal(h.calls.length, 1);
});

test("a stale value is served at once while one background refresh runs", async () => {
  const h = harness();
  await loaded(h, "a", "A1");
  h.clock.t = 1000;
  assert.equal(await h.cache.get("a"), "A1");
  assert.equal(await h.cache.get("a"), "A1");
  assert.equal(h.calls.length, 2);
  h.clock.t = 1100;
  h.calls[1].d.resolve("A2");
  await flush();
  assert.equal(h.cache.peek("a"), "A2");
  h.clock.t = 2099;
  assert.equal(await h.cache.get("a"), "A2");
  assert.equal(h.calls.length, 2);
});

test("a failed refresh keeps the stale value and reports the error", async () => {
  const h = harness();
  await loaded(h, "a", "A1");
  h.clock.t = 1200;
  assert.equal(await h.cache.get("a"), "A1");
  const boom = new Error("catalog down");
  h.calls[1].d.reject(boom);
  await flush();
  assert.deepEqual(h.refreshErrors, [["a", boom]]);
  assert.equal(h.cache.peek("a"), "A1");
  assert.equal(await h.cache.get("a"), "A1");
  assert.equal(h.calls.length, 3);
});

test("a failed refresh without onRefreshError is swallowed", async () => {
  const h = harness({ onRefreshError: undefined });
  await loaded(h, "a", "A1");
  h.clock.t = 1200;
  await h.cache.get("a");
  h.calls[1].d.reject(new Error("ignored"));
  await flush();
  assert.equal(await h.cache.get("a"), "A1");
});

test("an expired value is not served; get waits for a new load", async () => {
  const h = harness();
  await loaded(h, "a", "A1");
  h.clock.t = 1500;
  assert.equal(h.cache.peek("a"), undefined);
  assert.equal(h.cache.size, 0);
  const pending = track(h.cache.get("a"));
  await flush();
  assert.equal(pending.settled, false);
  assert.equal(h.calls.length, 2);
  h.calls[1].d.resolve("A2");
  await flush();
  assert.equal(pending.value, "A2");
});

test("staleMs of 0 means no stale window", async () => {
  const h = harness({ staleMs: 0 });
  await loaded(h, "a", "A1");
  h.clock.t = 1000;
  const pending = track(h.cache.get("a"));
  await flush();
  assert.equal(pending.settled, false);
});

test("a failed load rejects every waiter and caches nothing", async () => {
  const h = harness();
  const first = h.cache.get("a");
  const second = h.cache.get("a");
  const boom = new Error("nope");
  h.calls[0].d.reject(boom);
  await assert.rejects(first, (err) => err === boom);
  await assert.rejects(second, (err) => err === boom);
  assert.equal(h.cache.size, 0);
  assert.deepEqual(h.refreshErrors, []);
  const retry = h.cache.get("a");
  assert.equal(h.calls.length, 2);
  h.calls[1].d.resolve("A1");
  assert.equal(await retry, "A1");
});

test("a load that throws synchronously rejects the get", async () => {
  const boom = new Error("sync");
  const cache = new AsyncCache<string>({
    load: () => { throw boom; },
    ttlMs: 10,
    staleMs: 0,
    maxEntries: 1,
    now: () => 0,
  });
  let result: Promise<string> | undefined;
  assert.doesNotThrow(() => { result = cache.get("a"); });
  await assert.rejects(result!, (err) => err === boom);
});

test("a get after expiry joins the refresh already in flight", async () => {
  const h = harness();
  await loaded(h, "a", "A1");
  h.clock.t = 1200;
  await h.cache.get("a");
  h.clock.t = 1600;
  const waiting = h.cache.get("a");
  assert.equal(h.calls.length, 2);
  h.calls[1].d.resolve("A2");
  assert.equal(await waiting, "A2");
});

test("least recently used values are evicted past maxEntries", async () => {
  const h = harness({ maxEntries: 2 });
  await loaded(h, "a", "A");
  await loaded(h, "b", "B");
  await h.cache.get("a");
  await loaded(h, "c", "C");
  assert.equal(h.cache.peek("b"), undefined);
  assert.equal(h.cache.peek("a"), "A");
  assert.equal(h.cache.size, 2);
});

test("peek does not refresh recency", async () => {
  const h = harness({ maxEntries: 2 });
  await loaded(h, "a", "A");
  await loaded(h, "b", "B");
  h.cache.peek("a");
  await loaded(h, "c", "C");
  assert.equal(h.cache.peek("a"), undefined);
  assert.equal(h.cache.peek("b"), "B");
});

test("expired values are dropped before recency eviction", async () => {
  const h = harness({ maxEntries: 2, ttlMs: 100, staleMs: 0 });
  await loaded(h, "b", "B");
  h.clock.t = 60;
  await loaded(h, "a", "A");
  h.clock.t = 90;
  await h.cache.get("b");
  h.clock.t = 130;
  await loaded(h, "c", "C");
  assert.equal(h.cache.peek("a"), "A");
  assert.equal(h.cache.peek("c"), "C");
  assert.equal(h.cache.size, 2);
});

test("an evicted key's in-flight refresh still stores its result", async () => {
  const h = harness({ maxEntries: 1 });
  await loaded(h, "a", "A1");
  h.clock.t = 1100;
  await h.cache.get("a");
  const refresh = h.calls[1];
  await loaded(h, "b", "B1");
  assert.equal(h.cache.peek("a"), undefined);
  refresh.d.resolve("A2");
  await flush();
  assert.equal(h.cache.peek("a"), "A2");
  assert.equal(h.cache.peek("b"), undefined);
});

test("invalidate drops the value and detaches the in-flight load", async () => {
  const h = harness();
  await loaded(h, "a", "A1");
  assert.equal(h.cache.invalidate("a"), true);
  assert.equal(h.cache.invalidate("a"), false);
  const old = h.cache.get("a");
  assert.equal(h.cache.invalidate("a"), false);
  const fresh = h.cache.get("a");
  assert.equal(h.calls.length, 3);
  h.calls[1].d.resolve("OLD");
  assert.equal(await old, "OLD");
  assert.equal(h.cache.peek("a"), undefined);
  const joined = h.cache.get("a");
  assert.equal(h.calls.length, 3);
  h.calls[2].d.resolve("NEW");
  assert.deepEqual(await Promise.all([fresh, joined]), ["NEW", "NEW"]);
  assert.equal(h.cache.peek("a"), "NEW");
});

test("clear empties the cache and in-flight loads do not store", async () => {
  const h = harness();
  await loaded(h, "a", "A1");
  const pending = h.cache.get("b");
  h.cache.clear();
  assert.equal(h.cache.size, 0);
  assert.equal(h.cache.peek("a"), undefined);
  h.calls[1].d.resolve("B1");
  assert.equal(await pending, "B1");
  assert.equal(h.cache.peek("b"), undefined);
  const again = h.cache.get("b");
  assert.equal(h.calls.length, 3);
  h.calls[2].d.resolve("B2");
  assert.equal(await again, "B2");
});

test("size counts fresh and stale values only", async () => {
  const h = harness();
  await loaded(h, "a", "A");
  h.clock.t = 600;
  await loaded(h, "b", "B");
  h.clock.t = 1200;
  assert.equal(h.cache.size, 2);
  h.clock.t = 1500;
  assert.equal(h.cache.size, 1);
});
