import { test } from "node:test";
import assert from "node:assert/strict";
import { debounce } from "../src/debounce.js";
import { createFakeScheduler } from "./fake-scheduler.js";

test("trailing call after a single call", () => {
  const scheduler = createFakeScheduler();
  const calls = [];
  const debounced = debounce((x) => calls.push(x), 100, { scheduler });
  debounced("a");
  scheduler.advance(99);
  assert.deepEqual(calls, []);
  scheduler.advance(1);
  assert.deepEqual(calls, ["a"]);
});

test("leading only", () => {
  const scheduler = createFakeScheduler();
  const calls = [];
  const debounced = debounce((x) => calls.push(x), 100, { leading: true, trailing: false, scheduler });
  debounced("a");
  assert.deepEqual(calls, ["a"]);
  scheduler.advance(200);
  assert.deepEqual(calls, ["a"]);
});
