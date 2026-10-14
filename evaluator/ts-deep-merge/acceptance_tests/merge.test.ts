import { test } from "node:test";
import assert from "node:assert/strict";
import { deepMerge, deepMergeWith } from "../src/merge.ts";
import { DEFAULTS, loadConfig } from "../src/config.ts";

test("plain objects merge recursively, later sources win", () => {
  const out = deepMerge({ a: 1, n: { x: 1, y: 2 } }, { n: { y: 3, z: 4 } }, { a: 2 });
  assert.deepEqual(out, { a: 2, n: { x: 1, y: 3, z: 4 } });
});

test("null-prototype objects count as plain", () => {
  const target = Object.create(null);
  target.n = { a: 1 };
  const src = Object.create(null);
  src.n = Object.assign(Object.create(null), { b: 2 });
  const out = deepMerge(target, src);
  assert.equal(out.n.a, 1);
  assert.equal(out.n.b, 2);
});

test("result objects are new and inputs are untouched", () => {
  const target = { n: { x: 1 }, keep: { k: 1 } };
  const source = { n: { y: 2 }, only: { o: 1 } };
  const out = deepMerge(target, source);
  assert.notEqual(out, target);
  assert.notEqual(out.keep, target.keep);
  assert.notEqual(out.only, source.only);
  out.keep.k = 99;
  out.only.o = 99;
  assert.deepEqual(target, { n: { x: 1 }, keep: { k: 1 } });
  assert.deepEqual(source, { n: { y: 2 }, only: { o: 1 } });
});

test("arrays replace by default, with a new array holding the same items", () => {
  const item = { id: 1 };
  const source = { list: [item] };
  const out = deepMerge({ list: [0, 1] }, source);
  assert.deepEqual(out.list, [{ id: 1 }]);
  assert.notEqual(out.list, source.list);
  assert.equal(out.list[0], item);
});

test("arrays concat when asked", () => {
  const out = deepMergeWith({ arrays: "concat" }, { list: [1, 2], n: { l: ["a"] } }, { list: [3], n: { l: ["b"] } });
  assert.deepEqual(out, { list: [1, 2, 3], n: { l: ["a", "b"] } });
  const replaced = deepMergeWith({ arrays: "concat" }, { list: "x" }, { list: [1] });
  assert.deepEqual(replaced.list, [1]);
  assert.deepEqual(deepMergeWith({ arrays: "replace" }, { l: [1] }, { l: [2] }).l, [2]);
});

test("non-plain values are used by reference", () => {
  class Point { constructor(public_x: number) { this.x = public_x; } x: number; }
  const when = new Date(0);
  const map = new Map([["a", 1]]);
  const fn = () => 1;
  const p = new Point(1);
  const out = deepMerge({ when: new Date(5), p: { x: 9 } }, { when, map, fn, p });
  assert.equal(out.when, when);
  assert.equal(out.map, map);
  assert.equal(out.fn, fn);
  assert.equal(out.p, p);
});

test("a plain object replaces a non-plain value and vice versa", () => {
  assert.deepEqual(deepMerge({ a: new Date(0) }, { a: { b: 1 } }).a, { b: 1 });
  const d = new Date(0);
  assert.equal(deepMerge({ a: { b: 1 } }, { a: d }).a, d);
  assert.deepEqual(deepMerge({ a: 1 }, { a: { b: 1 } }).a, { b: 1 });
});

test("undefined is ignored, null is a value", () => {
  const out = deepMerge({ a: 1, n: { b: 2 } }, { a: undefined, c: undefined, n: { b: undefined } });
  assert.deepEqual(out, { a: 1, n: { b: 2 } });
  assert.equal(Object.prototype.hasOwnProperty.call(out, "c"), false);
  assert.deepEqual(deepMerge({ a: 1, n: { b: 2 } }, { a: null, n: null }), { a: null, n: null });
});

test("dangerous keys are skipped at every depth", () => {
  const evil = JSON.parse('{"__proto__": {"polluted": true}, "n": {"constructor": {"x": 1}, "prototype": 2, "ok": 1}}');
  const out = deepMerge({ n: { keep: 1 } }, evil);
  assert.equal(({} as Record<string, unknown>).polluted, undefined);
  assert.equal(Object.getPrototypeOf(out), Object.prototype);
  assert.deepEqual(Object.keys(out.n), ["keep", "ok"]);
  const fromTarget = deepMerge(JSON.parse('{"__proto__": {"bad": 1}, "a": 1}'));
  assert.deepEqual(Object.keys(fromTarget), ["a"]);
});

test("key order: target keys first, then new keys as introduced", () => {
  const out = deepMerge({ b: 1, a: 1 }, { c: 1, a: 2 }, { d: 1, b: 2 });
  assert.deepEqual(Object.keys(out), ["b", "a", "c", "d"]);
});

test("only own enumerable string keys are read", () => {
  const source: Record<string | symbol, unknown> = { own: 1 };
  Object.defineProperty(source, "hidden", { value: 1, enumerable: false });
  source[Symbol("s")] = 1;
  const out = deepMerge({}, source);
  assert.deepEqual(Object.keys(out), ["own"]);
  assert.equal(Object.getOwnPropertySymbols(out).length, 0);
});

test("null and undefined sources are skipped", () => {
  assert.deepEqual(deepMerge({ a: 1 }, null, undefined, { b: 2 }), { a: 1, b: 2 });
});

test("errors", () => {
  assert.throws(() => deepMerge(null), TypeError);
  assert.throws(() => deepMerge([1]), TypeError);
  assert.throws(() => deepMerge(new Date()), TypeError);
  assert.throws(() => deepMerge({}, [1]), TypeError);
  assert.throws(() => deepMerge({}, 5), TypeError);
  assert.throws(() => deepMergeWith({ arrays: "append" } as never, {}), RangeError);
});

test("loadConfig deep-merges its layers", () => {
  const cfg = loadConfig({ db: { pool: 20 } }, undefined, { service: { port: 9090 } });
  assert.deepEqual(cfg.db, { host: "localhost", port: 5432, pool: 20 });
  assert.deepEqual(cfg.service, { name: "api", port: 9090 });
  assert.deepEqual(loadConfig(), DEFAULTS);
  assert.notEqual(loadConfig().db, DEFAULTS.db);
});
