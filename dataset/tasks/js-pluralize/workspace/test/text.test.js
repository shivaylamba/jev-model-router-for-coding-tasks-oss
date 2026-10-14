import { test } from "node:test";
import assert from "node:assert/strict";
import { capitalize, truncate } from "../src/text.js";

test("capitalize", () => {
  assert.equal(capitalize("hello"), "Hello");
  assert.equal(capitalize(""), "");
});

test("truncate", () => {
  assert.equal(truncate("abcdef", 10), "abcdef");
  assert.equal(truncate("abcdef", 4), "abc…");
});
