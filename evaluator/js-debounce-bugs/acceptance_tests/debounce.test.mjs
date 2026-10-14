import { test } from "node:test";
import assert from "node:assert/strict";
import { debounce } from "../src/debounce.js";
import { createSearchBox } from "../src/searchbox.js";
import { createFakeScheduler } from "./fake-scheduler.mjs";

function setup(options = {}, wait = 100) {
  const scheduler = createFakeScheduler();
  const calls = [];
  const debounced = debounce(
    (...args) => {
      calls.push(args.length === 1 ? args[0] : args);
      return `r${calls.length}`;
    },
    wait,
    { ...options, scheduler },
  );
  return { scheduler, calls, debounced };
}

test("trailing call uses the most recent arguments", () => {
  const { scheduler, calls, debounced } = setup();
  debounced("a");
  scheduler.advance(50);
  debounced("b");
  scheduler.advance(50);
  debounced("c");
  scheduler.advance(99);
  assert.deepEqual(calls, []);
  scheduler.advance(1);
  assert.deepEqual(calls, ["c"]);
  scheduler.advance(500);
  assert.deepEqual(calls, ["c"]);
});

test("consecutive bursts each use their own latest arguments", () => {
  const { scheduler, calls, debounced } = setup();
  debounced(1);
  debounced(2);
  scheduler.advance(150);
  debounced(3);
  debounced(4);
  scheduler.advance(150);
  assert.deepEqual(calls, [2, 4]);
});

test("leading and trailing: a single call invokes once", () => {
  const { scheduler, calls, debounced } = setup({ leading: true });
  debounced("only");
  assert.deepEqual(calls, ["only"]);
  scheduler.advance(300);
  assert.deepEqual(calls, ["only"]);
});

test("leading and trailing: a burst invokes first and last", () => {
  const { scheduler, calls, debounced } = setup({ leading: true });
  debounced("a");
  scheduler.advance(30);
  debounced("b");
  scheduler.advance(30);
  debounced("c");
  scheduler.advance(100);
  assert.deepEqual(calls, ["a", "c"]);
  debounced("d");
  assert.deepEqual(calls, ["a", "c", "d"]);
  scheduler.advance(100);
  assert.deepEqual(calls, ["a", "c", "d"]);
});

test("leading only", () => {
  const { scheduler, calls, debounced } = setup({ leading: true, trailing: false });
  debounced("a");
  debounced("b");
  scheduler.advance(100);
  debounced("c");
  scheduler.advance(100);
  assert.deepEqual(calls, ["a", "c"]);
});

test("maxWait invokes with the latest arguments during a long burst", () => {
  const { scheduler, calls, debounced } = setup({ maxWait: 250 });
  for (let i = 0; i < 10; i++) {
    debounced(i);
    scheduler.advance(50);
  }
  assert.deepEqual(calls, [4, 9]);
  scheduler.advance(500);
  assert.deepEqual(calls, [4, 9]);
});

test("maxWait followed by a trailing call", () => {
  const { scheduler, calls, debounced } = setup({ maxWait: 250 });
  for (let i = 0; i <= 6; i++) {
    debounced(i);
    if (i < 6) scheduler.advance(50);
  }
  scheduler.advance(100);
  assert.deepEqual(calls, [4, 6]);
});

test("maxWait applies even without trailing", () => {
  const { scheduler, calls, debounced } = setup({ trailing: false, maxWait: 120 });
  debounced("a");
  scheduler.advance(60);
  debounced("b");
  scheduler.advance(60);
  assert.deepEqual(calls, ["b"]);
  scheduler.advance(500);
  assert.deepEqual(calls, ["b"]);
});

test("cancel drops the pending call", () => {
  const { scheduler, calls, debounced } = setup();
  debounced("a");
  debounced.cancel();
  scheduler.advance(1000);
  assert.deepEqual(calls, []);
});

test("cancel also stops the maxWait call", () => {
  const { scheduler, calls, debounced } = setup({ maxWait: 150 });
  debounced("a");
  scheduler.advance(80);
  debounced("b");
  debounced.cancel();
  scheduler.advance(1000);
  assert.deepEqual(calls, []);
});

test("a call after cancel starts a fresh burst", () => {
  const { scheduler, calls, debounced } = setup({ leading: true });
  debounced("a");
  scheduler.advance(10);
  debounced("b");
  debounced.cancel();
  debounced("c");
  assert.deepEqual(calls, ["a", "c"]);
  scheduler.advance(1000);
  assert.deepEqual(calls, ["a", "c"]);
  const second = setup();
  second.debounced("old");
  second.debounced.cancel();
  second.debounced("new");
  second.scheduler.advance(100);
  assert.deepEqual(second.calls, ["new"]);
});

test("flush invokes now with the latest arguments", () => {
  const { scheduler, calls, debounced } = setup({ maxWait: 300 });
  debounced("a");
  debounced("b");
  assert.equal(debounced.flush(), "r1");
  assert.deepEqual(calls, ["b"]);
  scheduler.advance(1000);
  assert.deepEqual(calls, ["b"]);
  assert.equal(debounced.flush(), "r1");
  assert.deepEqual(calls, ["b"]);
});

test("flush after a leading-only invocation does not invoke again", () => {
  const { calls, debounced } = setup({ leading: true });
  debounced("a");
  debounced.flush();
  assert.deepEqual(calls, ["a"]);
});

test("return value is the latest result", () => {
  const { scheduler, debounced } = setup();
  assert.equal(debounced("a"), undefined);
  scheduler.advance(100);
  assert.equal(debounced("b"), "r1");
});

test("this comes from the call whose arguments are used", () => {
  const scheduler = createFakeScheduler();
  const seen = [];
  const debounced = debounce(function (x) {
    seen.push([this.name, x]);
  }, 100, { scheduler });
  const first = { name: "first", run: debounced };
  const second = { name: "second", run: debounced };
  first.run(1);
  second.run(2);
  scheduler.advance(100);
  assert.deepEqual(seen, [["second", 2]]);
});

test("search box searches for the latest text and clear cancels", () => {
  const scheduler = createFakeScheduler();
  const queries = [];
  const box = createSearchBox((q) => queries.push(q), { scheduler });
  box.input("c");
  scheduler.advance(100);
  box.input("ca");
  scheduler.advance(100);
  box.input("cat ");
  scheduler.advance(250);
  assert.deepEqual(queries, ["cat"]);
  box.input("dog");
  box.clear();
  scheduler.advance(2000);
  assert.deepEqual(queries, ["cat"]);
});
