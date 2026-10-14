import { test } from "node:test";
import assert from "node:assert/strict";
import { initials } from "../src/names.ts";

test("spaces and hyphens", () => {
  assert.equal(initials("mary-jane van der berg"), "MJVDB");
});
test("uppercase", () => {
  assert.equal(initials("ada lovelace"), "AL");
});
test("extra spaces", () => {
  assert.equal(initials("  grace   hopper "), "GH");
});
test("blank", () => {
  assert.equal(initials(""), "");
  assert.equal(initials("   "), "");
});
