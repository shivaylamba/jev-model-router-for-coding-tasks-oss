import { test } from "node:test";
import assert from "node:assert/strict";
import { satisfies } from "../src/semver.ts";

test("exact versions", () => {
  assert.equal(satisfies("1.2.3", "1.2.3"), true);
  assert.equal(satisfies("1.2.3", "=1.2.3"), true);
  assert.equal(satisfies("1.2.3", "v1.2.3"), true);
  assert.equal(satisfies("v1.2.3", "1.2.3"), true);
  assert.equal(satisfies("1.2.4", "1.2.3"), false);
});

test("comparison operators with full versions", () => {
  assert.equal(satisfies("1.2.4", ">1.2.3"), true);
  assert.equal(satisfies("1.2.3", ">1.2.3"), false);
  assert.equal(satisfies("1.2.3", ">=1.2.3"), true);
  assert.equal(satisfies("1.2.2", "<1.2.3"), true);
  assert.equal(satisfies("1.2.3", "<1.2.3"), false);
  assert.equal(satisfies("1.2.3", "<=1.2.3"), true);
  assert.equal(satisfies("1.2.3", ">= 1.2.3"), true);
});

test("comparator sets are ANDed", () => {
  assert.equal(satisfies("1.5.0", ">=1.2.0 <2.0.0"), true);
  assert.equal(satisfies("2.0.0", ">=1.2.0 <2.0.0"), false);
  assert.equal(satisfies("1.1.9", ">=1.2.0   <2.0.0"), false);
  assert.equal(satisfies("1.9.0", ">= 1.2.0 < 2.0.0"), true);
});

test("comparison operators with partial versions", () => {
  assert.equal(satisfies("1.2.9", ">1.2"), false);
  assert.equal(satisfies("1.3.0", ">1.2"), true);
  assert.equal(satisfies("1.9.9", ">1"), false);
  assert.equal(satisfies("2.0.0", ">1"), true);
  assert.equal(satisfies("1.2.0", ">=1.2"), true);
  assert.equal(satisfies("1.2.0", "<1.2"), false);
  assert.equal(satisfies("1.1.99", "<1.2"), true);
  assert.equal(satisfies("1.2.99", "<=1.2"), true);
  assert.equal(satisfies("1.3.0", "<=1.2"), false);
  assert.equal(satisfies("1.99.0", "<=1"), true);
  assert.equal(satisfies("2.0.0", "<=1"), false);
});

test("x-ranges and missing parts", () => {
  assert.equal(satisfies("1.2.7", "1.2.x"), true);
  assert.equal(satisfies("1.2.0", "1.2"), true);
  assert.equal(satisfies("1.3.0", "1.2.X"), false);
  assert.equal(satisfies("1.9.9", "1.x"), true);
  assert.equal(satisfies("1.0.0", "1"), true);
  assert.equal(satisfies("2.0.0", "1.*.*"), false);
  assert.equal(satisfies("0.0.0", "*"), true);
  assert.equal(satisfies("9.9.9", "x"), true);
  assert.equal(satisfies("3.1.4", ""), true);
  assert.equal(satisfies("5.0.0", ">=*"), true);
  assert.equal(satisfies("5.0.0", ">*"), false);
  assert.equal(satisfies("0.0.0", "<*"), false);
});

test("tilde", () => {
  assert.equal(satisfies("1.2.3", "~1.2.3"), true);
  assert.equal(satisfies("1.2.9", "~1.2.3"), true);
  assert.equal(satisfies("1.3.0", "~1.2.3"), false);
  assert.equal(satisfies("1.2.2", "~1.2.3"), false);
  assert.equal(satisfies("1.2.0", "~1.2"), true);
  assert.equal(satisfies("1.3.0", "~1.2"), false);
  assert.equal(satisfies("1.9.0", "~1"), true);
  assert.equal(satisfies("2.0.0", "~1"), false);
});

test("caret", () => {
  assert.equal(satisfies("1.9.9", "^1.2.3"), true);
  assert.equal(satisfies("2.0.0", "^1.2.3"), false);
  assert.equal(satisfies("1.2.2", "^1.2.3"), false);
  assert.equal(satisfies("0.2.9", "^0.2.3"), true);
  assert.equal(satisfies("0.3.0", "^0.2.3"), false);
  assert.equal(satisfies("0.0.3", "^0.0.3"), true);
  assert.equal(satisfies("0.0.4", "^0.0.3"), false);
  assert.equal(satisfies("1.5.0", "^1.2"), true);
  assert.equal(satisfies("0.3.0", "^0.2"), false);
  assert.equal(satisfies("0.0.9", "^0.0"), true);
  assert.equal(satisfies("0.1.0", "^0.0"), false);
  assert.equal(satisfies("0.9.9", "^0.x"), true);
  assert.equal(satisfies("1.0.0", "^0"), false);
  assert.equal(satisfies("1.9.0", "^1.x"), true);
});

test("hyphen ranges", () => {
  assert.equal(satisfies("1.2.3", "1.2.3 - 2.3.4"), true);
  assert.equal(satisfies("2.3.4", "1.2.3 - 2.3.4"), true);
  assert.equal(satisfies("2.3.5", "1.2.3 - 2.3.4"), false);
  assert.equal(satisfies("1.2.0", "1.2 - 2.3.4"), true);
  assert.equal(satisfies("1.1.9", "1.2 - 2.3.4"), false);
  assert.equal(satisfies("2.3.9", "1.2.3 - 2.3"), true);
  assert.equal(satisfies("2.4.0", "1.2.3 - 2.3"), false);
  assert.equal(satisfies("2.9.9", "1.2.3 - 2"), true);
  assert.equal(satisfies("3.0.0", "1.2.3 - 2"), false);
  assert.equal(satisfies("0.0.1", "* - 1.0.0"), true);
  assert.equal(satisfies("99.0.0", "1.0.0 - *"), true);
});

test("alternatives with ||", () => {
  assert.equal(satisfies("1.2.5", "1.2.5 || >=2.0.0"), true);
  assert.equal(satisfies("2.1.0", "1.2.5 || >=2.0.0"), true);
  assert.equal(satisfies("1.3.0", "1.2.5 || >=2.0.0"), false);
  assert.equal(satisfies("0.5.0", "^1.0.0||^0.5.0"), true);
  assert.equal(satisfies("3.0.0", "1.0.0 - 1.5.0 || ~3.0"), true);
  assert.equal(satisfies("7.7.7", "1.0.0 ||"), true);
});

test("invalid versions throw TypeError", () => {
  assert.throws(() => satisfies("1.2", "*"), TypeError);
  assert.throws(() => satisfies("1.2.3-beta.1", "*"), TypeError);
  assert.throws(() => satisfies("01.2.3", "*"), TypeError);
});

test("invalid ranges throw TypeError", () => {
  assert.throws(() => satisfies("1.2.3", ">=1.2.3.4"), TypeError);
  assert.throws(() => satisfies("1.2.3", "~>1.2"), TypeError);
  assert.throws(() => satisfies("1.2.3", "1.2.3 -"), TypeError);
  assert.throws(() => satisfies("1.2.3", ">="), TypeError);
  assert.throws(() => satisfies("1.2.3", "1.x.3"), TypeError);
  assert.throws(() => satisfies("1.2.3", "01.2.3"), TypeError);
  assert.throws(() => satisfies("1.2.3", "1.2.3-beta"), TypeError);
  assert.throws(() => satisfies("1.2.3", "abc"), TypeError);
  assert.throws(() => satisfies("1.2.3", "1.2.3 - 2.0.0 - 3.0.0"), TypeError);
  assert.throws(() => satisfies("1.2.3", ">=1.0.0 - 2.0.0"), TypeError);
});
