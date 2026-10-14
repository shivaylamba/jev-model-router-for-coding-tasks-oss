import { test } from "node:test";
import assert from "node:assert/strict";
import { formatDuration } from "../src/duration.js";

const S = 1000, M = 60 * S, H = 60 * M, D = 24 * H;

test("long style defaults to two units", () => {
  assert.equal(formatDuration(H + 5 * M + 30 * S), "1 hour, 5 minutes");
  assert.equal(formatDuration(2 * D + 3 * H), "2 days, 3 hours");
});

test("singular and plural", () => {
  assert.equal(formatDuration(S), "1 second");
  assert.equal(formatDuration(2 * M + S), "2 minutes, 1 second");
});

test("zero units are skipped, not counted", () => {
  assert.equal(formatDuration(D + 5 * M), "1 day, 5 minutes");
  assert.equal(formatDuration(D + 7 * S), "1 day, 7 seconds");
  assert.equal(formatDuration(3 * H), "3 hours");
});

test("the remainder is dropped, not rounded", () => {
  assert.equal(formatDuration(59 * M + 59 * S + 999), "59 minutes, 59 seconds");
  assert.equal(formatDuration(H + 59 * M + 59 * S, { units: 1 }), "1 hour");
});

test("units option", () => {
  assert.equal(formatDuration(D + 2 * H + 3 * M + 4 * S, { units: 3 }), "1 day, 2 hours, 3 minutes");
  assert.equal(formatDuration(D + 2 * H + 3 * M + 4 * S, { units: 10 }), "1 day, 2 hours, 3 minutes, 4 seconds");
});

test("compact style", () => {
  assert.equal(formatDuration(H + 5 * M, { style: "compact" }), "1h 5m");
  assert.equal(formatDuration(D + 2 * H + 3 * M, { style: "compact", units: 3 }), "1d 2h 3m");
  assert.equal(formatDuration(1500, { style: "compact", smallest: "ms" }), "1s 500ms");
});

test("milliseconds hidden by default", () => {
  assert.equal(formatDuration(1500), "1 second");
  assert.equal(formatDuration(1500, { smallest: "ms" }), "1 second, 500 milliseconds");
  assert.equal(formatDuration(1, { smallest: "ms" }), "1 millisecond");
});

test("smallest unit", () => {
  assert.equal(formatDuration(H + 30 * S, { smallest: "m" }), "1 hour");
  assert.equal(formatDuration(D + 30 * M, { smallest: "h", units: 3 }), "1 day");
});

test("zero uses the smallest unit", () => {
  assert.equal(formatDuration(0), "0 seconds");
  assert.equal(formatDuration(999), "0 seconds");
  assert.equal(formatDuration(0, { style: "compact" }), "0s");
  assert.equal(formatDuration(30 * S, { smallest: "m" }), "0 minutes");
  assert.equal(formatDuration(0, { smallest: "ms", style: "compact" }), "0ms");
});

test("fractional milliseconds are floored", () => {
  assert.equal(formatDuration(2.9, { smallest: "ms" }), "2 milliseconds");
  assert.equal(formatDuration(0.5, { smallest: "ms" }), "0 milliseconds");
});

test("invalid input", () => {
  assert.throws(() => formatDuration("100"), TypeError);
  assert.throws(() => formatDuration(undefined), TypeError);
  assert.throws(() => formatDuration(-1), RangeError);
  assert.throws(() => formatDuration(NaN), RangeError);
  assert.throws(() => formatDuration(Infinity), RangeError);
});

test("invalid options", () => {
  assert.throws(() => formatDuration(1000, { units: 0 }), RangeError);
  assert.throws(() => formatDuration(1000, { units: 1.5 }), RangeError);
  assert.throws(() => formatDuration(1000, { style: "short" }), RangeError);
  assert.throws(() => formatDuration(1000, { smallest: "w" }), RangeError);
});
