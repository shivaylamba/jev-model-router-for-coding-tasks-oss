import { test } from "node:test";
import assert from "node:assert/strict";
import { formatCents } from "../src/money.ts";

test("basic USD", () => {
  assert.equal(formatCents(123456, "USD"), "$1,234.56");
  assert.equal(formatCents(100, "USD"), "$1.00");
});

test("small amounts keep two decimals", () => {
  assert.equal(formatCents(0, "USD"), "$0.00");
  assert.equal(formatCents(5, "USD"), "$0.05");
  assert.equal(formatCents(99, "GBP"), "£0.99");
});

test("thousands separators", () => {
  assert.equal(formatCents(99999, "USD"), "$999.99");
  assert.equal(formatCents(100000, "USD"), "$1,000.00");
  assert.equal(formatCents(123456789012, "EUR"), "€1,234,567,890.12");
});

test("currency symbols", () => {
  assert.equal(formatCents(250, "EUR"), "€2.50");
  assert.equal(formatCents(250, "GBP"), "£2.50");
});

test("negatives put the minus before the symbol", () => {
  assert.equal(formatCents(-123456, "USD"), "-$1,234.56");
  assert.equal(formatCents(-5, "GBP"), "-£0.05");
});

test("non-integers throw TypeError", () => {
  assert.throws(() => formatCents(12.5, "USD"), TypeError);
  assert.throws(() => formatCents(Number.NaN, "USD"), TypeError);
  assert.throws(() => formatCents(Infinity, "USD"), TypeError);
  assert.throws(() => formatCents("100" as unknown as number, "USD"), TypeError);
});

test("unknown currency throws RangeError", () => {
  assert.throws(() => formatCents(100, "JPY" as never), RangeError);
});
