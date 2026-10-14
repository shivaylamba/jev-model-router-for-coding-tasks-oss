import { test } from "node:test";
import assert from "node:assert/strict";
import { isPlainObject, mapValues } from "../src/object.js";

test("isPlainObject", () => {
  assert.equal(isPlainObject({}), true);
  assert.equal(isPlainObject(Object.create(null)), true);
  assert.equal(isPlainObject([]), false);
  assert.equal(isPlainObject(new Date()), false);
});

test("mapValues", () => {
  assert.deepEqual(mapValues({ a: 1, b: 2 }, (v) => v * 10), { a: 10, b: 20 });
});
