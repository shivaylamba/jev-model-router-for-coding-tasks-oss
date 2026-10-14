import { test } from "node:test";
import assert from "node:assert/strict";
import { normalizeHexColor } from "../src/color.ts";

test("six and eight digits are lowercased", () => {
  assert.equal(normalizeHexColor("#FF8800"), "#ff8800");
  assert.equal(normalizeHexColor("#aaBBcc"), "#aabbcc");
  assert.equal(normalizeHexColor("#11223344"), "#11223344");
  assert.equal(normalizeHexColor("#ABCDEFFF"), "#abcdefff");
});

test("three and four digits are expanded", () => {
  assert.equal(normalizeHexColor("#AbC"), "#aabbcc");
  assert.equal(normalizeHexColor("#f80"), "#ff8800");
  assert.equal(normalizeHexColor("#abcd"), "#aabbccdd");
  assert.equal(normalizeHexColor("#000F"), "#000000ff");
});

test("surrounding whitespace is ignored", () => {
  assert.equal(normalizeHexColor("  #fff\n"), "#ffffff");
});

test("invalid input gives null", () => {
  assert.equal(normalizeHexColor(""), null);
  assert.equal(normalizeHexColor("#"), null);
  assert.equal(normalizeHexColor("fff"), null);
  assert.equal(normalizeHexColor("ff8800"), null);
  assert.equal(normalizeHexColor("##fff"), null);
  assert.equal(normalizeHexColor("#ff"), null);
  assert.equal(normalizeHexColor("#fffff"), null);
  assert.equal(normalizeHexColor("#fffffff"), null);
  assert.equal(normalizeHexColor("#fffffffff"), null);
  assert.equal(normalizeHexColor("#ggg"), null);
  assert.equal(normalizeHexColor("#ff 880"), null);
  assert.equal(normalizeHexColor("0xff8800"), null);
  assert.equal(normalizeHexColor("red"), null);
});
