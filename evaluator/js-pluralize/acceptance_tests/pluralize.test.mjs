import { test } from "node:test";
import assert from "node:assert/strict";
import { pluralize } from "../src/text.js";

test("singular only for exactly one", () => {
  assert.equal(pluralize(1, "file"), "1 file");
  assert.equal(pluralize(0, "file"), "0 files");
  assert.equal(pluralize(2, "file"), "2 files");
  assert.equal(pluralize(-1, "file"), "-1 files");
  assert.equal(pluralize(1.5, "file"), "1.5 files");
});

test("es endings", () => {
  assert.equal(pluralize(2, "bus"), "2 buses");
  assert.equal(pluralize(2, "box"), "2 boxes");
  assert.equal(pluralize(2, "quiz"), "2 quizes");
  assert.equal(pluralize(2, "match"), "2 matches");
  assert.equal(pluralize(2, "dish"), "2 dishes");
});

test("consonant plus y", () => {
  assert.equal(pluralize(3, "city"), "3 cities");
  assert.equal(pluralize(3, "directory"), "3 directories");
});

test("vowel plus y just adds s", () => {
  assert.equal(pluralize(3, "day"), "3 days");
  assert.equal(pluralize(3, "key"), "3 keys");
});

test("explicit plural", () => {
  assert.equal(pluralize(2, "child", "children"), "2 children");
  assert.equal(pluralize(1, "child", "children"), "1 child");
  assert.equal(pluralize(0, "person", "people"), "0 people");
});

test("invalid count", () => {
  assert.throws(() => pluralize(NaN, "file"), TypeError);
  assert.throws(() => pluralize(Infinity, "file"), TypeError);
  assert.throws(() => pluralize("2", "file"), TypeError);
});
