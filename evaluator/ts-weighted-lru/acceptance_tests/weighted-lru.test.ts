import { test } from "node:test";
import assert from "node:assert/strict";
import { WeightedLRU } from "../src/weightedLru.ts";

function sized(maxWeight: number, evicted: Array<[string, string]> = []) {
  return new WeightedLRU<string, string>({
    maxWeight,
    weigh: (value) => value.length,
    onEvict: (key, value) => evicted.push([key, value]),
  });
}

test("default weight is 1 per entry", () => {
  const cache = new WeightedLRU<string, number>({ maxWeight: 2 });
  assert.equal(cache.set("a", 1), true);
  cache.set("b", 2);
  cache.set("c", 3);
  assert.deepEqual(cache.keys(), ["b", "c"]);
  assert.equal(cache.totalWeight, 2);
  assert.equal(cache.size, 2);
});

test("evicts least recently used until the weight fits, calling onEvict in order", () => {
  const evicted: Array<[string, string]> = [];
  const cache = sized(10, evicted);
  cache.set("a", "xxx");
  cache.set("b", "xxx");
  cache.set("c", "xxx");
  cache.get("a");
  assert.equal(cache.set("d", "xxxxxx"), true);
  assert.deepEqual(evicted, [["b", "xxx"], ["c", "xxx"]]);
  assert.deepEqual(cache.keys(), ["a", "d"]);
  assert.equal(cache.totalWeight, 9);
  assert.equal(cache.stats().evictions, 2);
});

test("weigh receives the value and the key", () => {
  const seen: Array<[number, string]> = [];
  const cache = new WeightedLRU<string, number>({ maxWeight: 100, weigh: (value, key) => { seen.push([value, key]); return value; } });
  cache.set("k", 7);
  assert.deepEqual(seen, [[7, "k"]]);
  assert.equal(cache.totalWeight, 7);
});

test("an oversize entry is rejected and leaves the cache untouched", () => {
  const evicted: Array<[string, string]> = [];
  const cache = sized(5, evicted);
  cache.set("a", "xx");
  cache.set("b", "xx");
  assert.equal(cache.set("a", "xxxxxx"), false);
  assert.equal(cache.peek("a"), "xx");
  assert.deepEqual(cache.keys(), ["a", "b"]);
  assert.equal(cache.totalWeight, 4);
  assert.deepEqual(evicted, []);
  assert.equal(cache.set("c", "xxxxx"), true);
  assert.deepEqual(cache.keys(), ["c"]);
});

test("replacing a key frees its old weight first and does not call onEvict", () => {
  const evicted: Array<[string, string]> = [];
  const cache = sized(10, evicted);
  cache.set("a", "xxxx");
  cache.set("b", "xxxx");
  cache.set("a", "xxxxxx");
  assert.deepEqual(evicted, []);
  assert.deepEqual(cache.keys(), ["b", "a"]);
  assert.equal(cache.totalWeight, 10);
  assert.equal(cache.get("a"), "xxxxxx");
});

test("the entry just set is never the one evicted", () => {
  const evicted: Array<[string, string]> = [];
  const cache = sized(4, evicted);
  cache.set("a", "xx");
  cache.set("b", "xxxx");
  assert.deepEqual(evicted, [["a", "xx"]]);
  assert.deepEqual(cache.keys(), ["b"]);
});

test("onEvict runs after the entry is removed", () => {
  const states: boolean[] = [];
  const cache: WeightedLRU<string, string> = new WeightedLRU<string, string>({
    maxWeight: 1,
    onEvict: (key) => states.push(cache.has(key)),
  });
  cache.set("a", "1");
  cache.set("b", "2");
  assert.deepEqual(states, [false]);
});

test("peek and has do not change recency or stats", () => {
  const cache = sized(6);
  cache.set("a", "xx");
  cache.set("b", "xx");
  cache.set("c", "xx");
  assert.equal(cache.peek("a"), "xx");
  assert.equal(cache.has("a"), true);
  assert.equal(cache.peek("zz"), undefined);
  assert.deepEqual(cache.stats(), { hits: 0, misses: 0, evictions: 0 });
  cache.set("d", "xx");
  assert.equal(cache.has("a"), false);
});

test("get counts hits and misses and refreshes recency", () => {
  const cache = sized(100);
  cache.set("a", "x");
  cache.set("b", "x");
  assert.equal(cache.get("a"), "x");
  assert.equal(cache.get("nope"), undefined);
  assert.equal(cache.get("a"), "x");
  assert.deepEqual(cache.keys(), ["b", "a"]);
  assert.deepEqual(cache.stats(), { hits: 2, misses: 1, evictions: 0 });
});

test("delete and clear do not call onEvict; clear keeps stats", () => {
  const evicted: Array<[string, string]> = [];
  const cache = sized(10, evicted);
  cache.set("a", "xxx");
  cache.set("b", "xxx");
  cache.get("a");
  assert.equal(cache.delete("a"), true);
  assert.equal(cache.delete("a"), false);
  assert.equal(cache.totalWeight, 3);
  cache.clear();
  assert.equal(cache.size, 0);
  assert.equal(cache.totalWeight, 0);
  assert.deepEqual(evicted, []);
  assert.deepEqual(cache.stats(), { hits: 1, misses: 0, evictions: 0 });
});

test("zero-weight entries are allowed", () => {
  const cache = sized(2);
  cache.set("a", "");
  cache.set("b", "xx");
  assert.deepEqual(cache.keys(), ["a", "b"]);
  assert.equal(cache.totalWeight, 2);
});

test("invalid options and weights throw RangeError", () => {
  for (const maxWeight of [0, -1, Number.NaN, Number.POSITIVE_INFINITY]) {
    assert.throws(() => new WeightedLRU({ maxWeight }), RangeError);
  }
  for (const weight of [-1, Number.NaN, Number.POSITIVE_INFINITY]) {
    const cache = new WeightedLRU<string, number>({ maxWeight: 10, weigh: () => weight });
    assert.throws(() => cache.set("a", 1), RangeError);
    assert.equal(cache.size, 0);
  }
});

test("fractional weights", () => {
  const cache = new WeightedLRU<string, number>({ maxWeight: 1, weigh: (value) => value });
  cache.set("a", 0.5);
  cache.set("b", 0.5);
  assert.deepEqual(cache.keys(), ["a", "b"]);
  cache.set("c", 0.25);
  assert.deepEqual(cache.keys(), ["b", "c"]);
});
