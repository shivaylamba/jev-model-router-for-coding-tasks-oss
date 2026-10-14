import { test } from "node:test";
import assert from "node:assert/strict";
import { daysInMonth, isLeapYear } from "../src/dates.ts";

test("leap years", () => {
  assert.equal(isLeapYear(2024), true);
  assert.equal(isLeapYear(1900), false);
  assert.equal(isLeapYear(2000), true);
});

test("days in month", () => {
  assert.equal(daysInMonth(2023, 2), 28);
  assert.equal(daysInMonth(2024, 2), 29);
  assert.equal(daysInMonth(2024, 4), 30);
  assert.equal(daysInMonth(2024, 12), 31);
});
