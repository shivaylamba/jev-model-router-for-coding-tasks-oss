import { test } from "node:test";
import assert from "node:assert/strict";
import { formatBytes, formatCount } from "../src/format.ts";

test("formatBytes", () => {
  assert.equal(formatBytes(0), "0 B");
  assert.equal(formatBytes(1023), "1023 B");
  assert.equal(formatBytes(1536), "1.5 KB");
  assert.equal(formatBytes(5 * 1024 * 1024), "5.0 MB");
  assert.throws(() => formatBytes(-1), RangeError);
});

test("formatCount", () => {
  assert.equal(formatCount(999), "999");
  assert.equal(formatCount(1234567), "1,234,567");
});
