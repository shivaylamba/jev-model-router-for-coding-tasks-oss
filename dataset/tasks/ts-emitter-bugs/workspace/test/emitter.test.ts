import { test } from "node:test";
import assert from "node:assert/strict";
import { Emitter } from "../src/emitter.ts";
import { Store } from "../src/store.ts";

test("on and emit", () => {
  const emitter = new Emitter();
  const calls: unknown[][] = [];
  emitter.on("save", (...args) => calls.push(args));
  assert.equal(emitter.emit("save", 1, "a"), true);
  assert.deepEqual(calls, [[1, "a"]]);
  assert.equal(emitter.emit("other"), false);
});

test("off removes an on listener", () => {
  const emitter = new Emitter();
  let count = 0;
  const listener = () => count++;
  emitter.on("x", listener);
  emitter.off("x", listener);
  emitter.emit("x");
  assert.equal(count, 0);
});

test("store notifies subscribers", () => {
  const store = new Store();
  const seen: unknown[] = [];
  store.subscribe((key, value) => seen.push([key, value]));
  store.set("theme", "dark");
  store.set("theme", "dark");
  assert.deepEqual(seen, [["theme", "dark"]]);
});
