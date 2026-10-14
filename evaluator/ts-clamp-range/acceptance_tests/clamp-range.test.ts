import { test } from "node:test";
import assert from "node:assert/strict";
import { clamp, range } from "../src/numbers.ts";

test("clamp inside, below and above", () => {
  assert.equal(clamp(5, 0, 10), 5);
  assert.equal(clamp(-3, 0, 10), 0);
  assert.equal(clamp(42, 0, 10), 10);
  assert.equal(clamp(2.5, 1.5, 2), 2);
});

test("clamp with min equal to max", () => {
  assert.equal(clamp(7, 3, 3), 3);
});

test("clamp rejects min greater than max", () => {
  assert.throws(() => clamp(1, 5, 2), RangeError);
});

test("range with only stop", () => {
  assert.deepEqual(range(5), [0, 1, 2, 3, 4]);
  assert.deepEqual(range(0), []);
  assert.deepEqual(range(-3), []);
});

test("range with start and stop", () => {
  assert.deepEqual(range(2, 6), [2, 3, 4, 5]);
  assert.deepEqual(range(6, 2), []);
});

test("range with a positive step", () => {
  assert.deepEqual(range(0, 10, 3), [0, 3, 6, 9]);
  assert.deepEqual(range(1, 2, 5), [1]);
});

test("range with a negative step", () => {
  assert.deepEqual(range(5, 0, -2), [5, 3, 1]);
  assert.deepEqual(range(3, -3, -3), [3, 0]);
  assert.deepEqual(range(0, 5, -1), []);
});

test("range rejects a zero step", () => {
  assert.throws(() => range(0, 5, 0), RangeError);
});
