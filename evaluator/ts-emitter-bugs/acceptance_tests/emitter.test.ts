import { test } from "node:test";
import assert from "node:assert/strict";
import { Emitter } from "../src/emitter.ts";
import { Store } from "../src/store.ts";

test("off removes a once listener before it fires", () => {
  const emitter = new Emitter();
  let calls = 0;
  const handler = () => calls++;
  emitter.once("change", handler);
  assert.equal(emitter.listenerCount("change"), 1);
  emitter.off("change", handler);
  assert.equal(emitter.listenerCount("change"), 0);
  assert.equal(emitter.emit("change"), false);
  assert.equal(calls, 0);
});

test("the function returned by once cancels it", () => {
  const emitter = new Emitter();
  let calls = 0;
  const cancel = emitter.once("x", () => calls++);
  cancel();
  emitter.emit("x");
  assert.equal(calls, 0);
});

test("once fires exactly once, even when it re-emits", () => {
  const emitter = new Emitter();
  let calls = 0;
  emitter.once("tick", () => {
    calls++;
    emitter.emit("tick");
  });
  emitter.emit("tick");
  emitter.emit("tick");
  assert.equal(calls, 1);
  assert.equal(emitter.listenerCount("tick"), 0);
});

test("consecutive once listeners all fire", () => {
  const emitter = new Emitter();
  const calls: string[] = [];
  emitter.once("x", () => calls.push("a"));
  emitter.once("x", () => calls.push("b"));
  emitter.on("x", () => calls.push("c"));
  emitter.emit("x");
  emitter.emit("x");
  assert.deepEqual(calls, ["a", "b", "c", "c"]);
});

test("self-removal does not skip the next listener", () => {
  const emitter = new Emitter();
  const calls: string[] = [];
  const unsubscribe = emitter.on("x", () => {
    calls.push("a");
    unsubscribe();
  });
  emitter.on("x", () => calls.push("b"));
  emitter.on("x", () => calls.push("c"));
  emitter.emit("x");
  assert.deepEqual(calls, ["a", "b", "c"]);
  emitter.emit("x");
  assert.deepEqual(calls, ["a", "b", "c", "b", "c"]);
});

test("a listener removed during emit before its turn is not called", () => {
  const emitter = new Emitter();
  const calls: string[] = [];
  const later = () => calls.push("later");
  emitter.on("x", () => {
    calls.push("first");
    emitter.off("x", later);
  });
  emitter.on("x", later);
  emitter.on("x", () => calls.push("last"));
  emitter.emit("x");
  assert.deepEqual(calls, ["first", "last"]);
});

test("removing an earlier listener during emit does not affect later ones", () => {
  const emitter = new Emitter();
  const calls: string[] = [];
  const first = () => calls.push("first");
  emitter.on("x", first);
  emitter.on("x", () => {
    calls.push("second");
    emitter.off("x", first);
  });
  emitter.on("x", () => calls.push("third"));
  emitter.emit("x");
  assert.deepEqual(calls, ["first", "second", "third"]);
});

test("listeners added during emit run from the next emit", () => {
  const emitter = new Emitter();
  const calls: string[] = [];
  let added = false;
  emitter.on("x", () => {
    calls.push("outer");
    if (!added) {
      added = true;
      emitter.on("x", () => calls.push("inner"));
    }
  });
  emitter.emit("x");
  assert.deepEqual(calls, ["outer"]);
  emitter.emit("x");
  assert.deepEqual(calls, ["outer", "outer", "inner"]);
});

test("a once listener re-registering itself fires on the next emit", () => {
  const emitter = new Emitter();
  let calls = 0;
  const handler = () => {
    calls++;
    emitter.once("x", handler);
  };
  emitter.once("x", handler);
  emitter.emit("x");
  assert.equal(calls, 1);
  emitter.emit("x");
  assert.equal(calls, 2);
});

test("duplicate registrations", () => {
  const emitter = new Emitter();
  let calls = 0;
  const handler = () => calls++;
  emitter.on("x", handler);
  emitter.once("x", handler);
  emitter.emit("x");
  assert.equal(calls, 2);
  emitter.emit("x");
  assert.equal(calls, 3);
  emitter.off("x", handler);
  assert.equal(emitter.listenerCount("x"), 0);
});

test("off removes the earliest registration, on or once", () => {
  const emitter = new Emitter();
  const calls: string[] = [];
  const handler = (tag: unknown) => calls.push(String(tag));
  emitter.once("x", handler);
  emitter.on("x", handler);
  emitter.off("x", handler);
  emitter.emit("x", "t");
  emitter.emit("x", "u");
  assert.deepEqual(calls, ["t", "u"]);
});

test("store: two subscribeOnce callbacks both run", () => {
  const store = new Store();
  const seen: string[] = [];
  store.subscribeOnce((key) => seen.push(`one:${key}`));
  store.subscribeOnce((key) => seen.push(`two:${key}`));
  store.set("lang", "en");
  store.set("lang", "fr");
  assert.deepEqual(seen, ["one:lang", "two:lang"]);
});
