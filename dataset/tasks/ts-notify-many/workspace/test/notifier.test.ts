import { test } from "node:test";
import assert from "node:assert/strict";
import { MemoryTransport, Notifier } from "../src/notifier.ts";
import { dispatchAlert } from "../src/alerts.ts";
import { sendDigest } from "../src/digest.ts";

test("notify trims and sends", () => {
  const transport = new MemoryTransport();
  new Notifier(transport).notify("  ops@example.com ", "hi");
  assert.deepEqual(transport.sent, [{ recipient: "ops@example.com", message: "hi" }]);
});

test("blank recipient is rejected", () => {
  const notifier = new Notifier(new MemoryTransport());
  assert.throws(() => notifier.notify("  ", "hi"), TypeError);
});

test("alerts page only on critical", () => {
  const transport = new MemoryTransport();
  const notifier = new Notifier(transport);
  assert.equal(dispatchAlert(notifier, "oncall@example.com", { service: "db", level: "warning", text: "slow" }), false);
  assert.equal(dispatchAlert(notifier, "oncall@example.com", { service: "db", level: "critical", text: "down" }), true);
  assert.deepEqual(transport.sent, [{ recipient: "oncall@example.com", message: "[db] down" }]);
});

test("digest goes to every subscriber", () => {
  const transport = new MemoryTransport();
  sendDigest(new Notifier(transport), ["a@example.com", "b@example.com"], ["one"]);
  assert.equal(transport.sent.length, 2);
  assert.equal(transport.sent[1].message, "- one");
});
