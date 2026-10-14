import { test } from "node:test";
import assert from "node:assert/strict";
import { mean, sum } from "../src/numbers.ts";

test("sum", () => {
  assert.equal(sum([]), 0);
  assert.equal(sum([1, 2, 3.5]), 6.5);
});

test("mean", () => {
  assert.equal(mean([2, 4]), 3);
  assert.throws(() => mean([]), RangeError);
});
