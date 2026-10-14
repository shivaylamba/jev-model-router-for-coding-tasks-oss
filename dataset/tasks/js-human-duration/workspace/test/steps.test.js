import { test } from "node:test";
import assert from "node:assert/strict";
import { slowestStep, stepDurations } from "../src/steps.js";

const steps = [
  { name: "install", startedAt: 0, finishedAt: 4000 },
  { name: "build", startedAt: 4000, finishedAt: 9000 },
  { name: "test", startedAt: 9000, finishedAt: 14000 },
];

test("stepDurations", () => {
  assert.deepEqual(stepDurations(steps).map((d) => d.ms), [4000, 5000, 5000]);
});

test("slowestStep keeps the first of a tie", () => {
  assert.equal(slowestStep(steps).name, "build");
  assert.equal(slowestStep([]), null);
});
