import { test } from "node:test";
import assert from "node:assert/strict";
import { parseEmailList } from "../src/emails.js";

test("splits on commas, semicolons and whitespace", () => {
  const text = " ada@example.com,bob@example.org ;\n carol@example.net\t\tdan@example.io;;, ";
  assert.deepEqual(parseEmailList(text), {
    valid: ["ada@example.com", "bob@example.org", "carol@example.net", "dan@example.io"],
    invalid: [],
  });
});

test("empty input", () => {
  assert.deepEqual(parseEmailList(""), { valid: [], invalid: [] });
  assert.deepEqual(parseEmailList(" ,; \n"), { valid: [], invalid: [] });
});

test("valid local parts and domains", () => {
  const text = "first.last+tag@mail.example.co.uk o'neil@example.com a_b%c-d@sub-domain.example.com x@a1.io";
  assert.deepEqual(parseEmailList(text), {
    valid: ["first.last+tag@mail.example.co.uk", "a_b%c-d@sub-domain.example.com", "x@a1.io"],
    invalid: ["o'neil@example.com"],
  });
});

test("invalid addresses keep their order and duplicates", () => {
  const text = "nope a@b@example.com nope @example.com ada@ ada@localhost";
  assert.deepEqual(parseEmailList(text).invalid, ["nope", "a@b@example.com", "nope", "@example.com", "ada@", "ada@localhost"]);
});

test("local part dot rules", () => {
  const result = parseEmailList(".ada@example.com ada.@example.com a..da@example.com a.da@example.com");
  assert.deepEqual(result.valid, ["a.da@example.com"]);
  assert.equal(result.invalid.length, 3);
});

test("local part length limit", () => {
  const ok = `${"a".repeat(64)}@example.com`;
  const long = `${"a".repeat(65)}@example.com`;
  assert.deepEqual(parseEmailList(`${ok} ${long}`), { valid: [ok], invalid: [long] });
});

test("domain label rules", () => {
  const result = parseEmailList(
    "a@-example.com a@example-.com a@exa_mple.com a@example..com a@example.c a@example.c0m a@.example.com a@example.com.",
  );
  assert.deepEqual(result.valid, []);
  assert.equal(result.invalid.length, 8);
  const label63 = "b".repeat(63);
  const label64 = "b".repeat(64);
  assert.deepEqual(parseEmailList(`a@${label63}.com a@${label64}.com`).valid, [`a@${label63}.com`]);
});

test("case-insensitive de-duplication keeps the first spelling", () => {
  const text = "Ada@Example.com bob@example.com ada@example.COM ADA@EXAMPLE.COM bob@example.com";
  assert.deepEqual(parseEmailList(text), { valid: ["Ada@Example.com", "bob@example.com"], invalid: [] });
});

test("display names are not supported", () => {
  assert.deepEqual(parseEmailList("Ada <ada@example.com>"), { valid: [], invalid: ["Ada", "<ada@example.com>"] });
});
