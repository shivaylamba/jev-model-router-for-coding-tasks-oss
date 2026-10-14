import { test } from "node:test";
import assert from "node:assert/strict";
import { pick, omit } from "../src/object.js";

test("pick keeps the listed keys", () => {
  assert.deepEqual(pick({ a: 1, b: 2, c: 3 }, ["a", "c"]), { a: 1, c: 3 });
});

test("pick follows the order of keys", () => {
  assert.deepEqual(Object.keys(pick({ a: 1, b: 2, c: 3 }, ["c", "a"])), ["c", "a"]);
});

test("pick ignores missing keys and keeps undefined values that exist", () => {
  const result = pick({ a: 1, u: undefined }, ["a", "zzz", "u"]);
  assert.deepEqual(result, { a: 1, u: undefined });
  assert.equal(Object.hasOwn(result, "zzz"), false);
});

test("pick ignores inherited and non-enumerable properties", () => {
  const proto = { inherited: 1 };
  const obj = Object.create(proto);
  obj.own = 2;
  Object.defineProperty(obj, "hidden", { value: 3, enumerable: false });
  assert.deepEqual(pick(obj, ["own", "inherited", "hidden", "toString"]), { own: 2 });
});

test("omit drops the listed keys and keeps the rest in order", () => {
  const result = omit({ a: 1, b: 2, c: 3 }, ["b", "missing"]);
  assert.deepEqual(result, { a: 1, c: 3 });
  assert.deepEqual(Object.keys(result), ["a", "c"]);
});

test("omit only copies own enumerable properties", () => {
  const obj = Object.create({ inherited: 1 });
  obj.own = 2;
  Object.defineProperty(obj, "hidden", { value: 3, enumerable: false });
  const result = omit(obj, []);
  assert.deepEqual(Object.keys(result), ["own"]);
  assert.equal("inherited" in result, false);
});

test("inputs are not mutated and results are new objects", () => {
  const obj = { a: 1, b: 2 };
  const keys = ["a"];
  const picked = pick(obj, keys);
  const omitted = omit(obj, keys);
  assert.deepEqual(obj, { a: 1, b: 2 });
  assert.deepEqual(keys, ["a"]);
  assert.notEqual(picked, obj);
  assert.notEqual(omitted, obj);
  assert.notEqual(omit(obj, []), obj);
});
