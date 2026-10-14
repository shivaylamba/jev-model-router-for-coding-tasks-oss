import { test } from "node:test";
import assert from "node:assert/strict";
import { LRUCache } from "../src/lru.ts";

test("evicts the least recently used entry", () => {
  const cache = new LRUCache<string, number>(2);
  cache.set("a", 1);
  cache.set("b", 2);
  cache.get("a");
  cache.set("c", 3);
  assert.equal(cache.has("b"), false);
  assert.equal(cache.get("a"), 1);
  assert.equal(cache.size, 2);
});

test("rejects a bad capacity", () => {
  assert.throws(() => new LRUCache(0), RangeError);
});
