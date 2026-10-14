import { test } from "node:test";
import assert from "node:assert/strict";
import { MemoryTransport, Notifier } from "../src/notifier.ts";
import { dispatchAlert } from "../src/alerts.ts";
import { sendDigest } from "../src/digest.ts";

function setup() {
  const transport = new MemoryTransport();
  return { transport, notifier: new Notifier(transport) };
}

test("single string still works and returns 1", () => {
  const { transport, notifier } = setup();
  assert.equal(notifier.notify(" ops@example.com ", "hi"), 1);
  assert.deepEqual(transport.sent, [{ recipient: "ops@example.com", message: "hi" }]);
});

test("array sends to each recipient in order", () => {
  const { transport, notifier } = setup();
  assert.equal(notifier.notify(["a@example.com", "b@example.com", "c@example.com"], "m"), 3);
  assert.deepEqual(transport.sent.map((s) => s.recipient), ["a@example.com", "b@example.com", "c@example.com"]);
  assert.ok(transport.sent.every((s) => s.message === "m"));
});

test("duplicates are sent once, case-insensitively, keeping the first spelling", () => {
  const { transport, notifier } = setup();
  const count = notifier.notify(["Ann@Example.com", "bob@example.com", " ann@example.com", "BOB@example.com "], "m");
  assert.equal(count, 2);
  assert.deepEqual(transport.sent.map((s) => s.recipient), ["Ann@Example.com", "bob@example.com"]);
});

test("empty array sends nothing", () => {
  const { transport, notifier } = setup();
  assert.equal(notifier.notify([], "m"), 0);
  assert.equal(transport.sent.length, 0);
});

test("a blank entry throws TypeError before anything is sent", () => {
  const { transport, notifier } = setup();
  assert.throws(() => notifier.notify(["a@example.com", "  "], "m"), TypeError);
  assert.equal(transport.sent.length, 0);
  assert.throws(() => notifier.notify("", "m"), TypeError);
});

test("existing callers are unchanged", () => {
  const { transport, notifier } = setup();
  assert.equal(dispatchAlert(notifier, "oncall@example.com", { service: "api", level: "critical", text: "5xx" }), true);
  sendDigest(notifier, ["x@example.com", "y@example.com"], []);
  assert.deepEqual(transport.sent, [
    { recipient: "oncall@example.com", message: "[api] 5xx" },
    { recipient: "x@example.com", message: "Nothing new today." },
    { recipient: "y@example.com", message: "Nothing new today." },
  ]);
});
