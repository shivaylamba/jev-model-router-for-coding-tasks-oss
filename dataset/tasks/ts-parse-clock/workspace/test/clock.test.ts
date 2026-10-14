import { test } from "node:test";
import assert from "node:assert/strict";
import { formatClock } from "../src/clock.ts";

test("formatClock pads hours and minutes", () => {
  assert.equal(formatClock(0), "00:00");
  assert.equal(formatClock(19 * 60 + 5), "19:05");
});

test("formatClock rejects out-of-range minutes", () => {
  assert.throws(() => formatClock(1440), RangeError);
});
