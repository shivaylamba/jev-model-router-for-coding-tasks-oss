import { test } from "node:test";
import assert from "node:assert/strict";
import { renderTable } from "../src/table.ts";
import { packageReport } from "../src/report.ts";

const lines = (s: string) => s.split("\n");

test("basic layout pads every line to the table width", () => {
  assert.equal(renderTable([["a", "bbb"], ["cc", "d"]]), "a  | bbb\ncc | d  ");
});

test("empty input", () => {
  assert.equal(renderTable([]), "");
  assert.equal(renderTable([[], []]), "");
});

test("ragged rows are padded with empty cells", () => {
  assert.deepEqual(lines(renderTable([["a", "b", "c"], ["d"]])), ["a | b | c", "d |   |  "]);
});

test("header separator", () => {
  assert.deepEqual(lines(renderTable([["id", "name"], ["1", "ada"]], { header: true })), [
    "id | name",
    "---+-----",
    "1  | ada ",
  ]);
});

test("alignment", () => {
  const out = renderTable([["name", "count", "state"], ["x", "7", "ab"]], { align: ["left", "right", "center"] });
  assert.deepEqual(lines(out), ["name | count | state", "x    |     7 |  ab  "]);
});

test("missing and extra align entries", () => {
  assert.equal(renderTable([["aaa", "bbb"], ["a", "b"]], { align: ["right"] }), "aaa | bbb\n  a | b  ");
  assert.equal(renderTable([["aa"], ["b"]], { align: ["center", "right", "right"] }), "aa\nb ");
});

test("spaces collapse and natural width uses single spaces", () => {
  assert.equal(renderTable([["  a   b  ", "c"]]), "a b | c");
});

test("wraps on words to fit maxWidth", () => {
  const out = renderTable(
    [["name", "description"], ["alpha", "the first package in the list"], ["b", "x"]],
    { maxWidth: 20, header: true },
  );
  assert.deepEqual(lines(out), [
    "name  | description ",
    "------+-------------",
    "alpha | the first   ",
    "      | package in  ",
    "      | the list    ",
    "b     | x           ",
  ]);
  for (const line of lines(out)) assert.equal(line.length, 20);
});

test("the widest column shrinks first, rightmost on ties", () => {
  assert.deepEqual(lines(renderTable([["aaaa", "bbbb"]], { maxWidth: 8 })), ["aaa | bb", "a   | bb"]);
  assert.deepEqual(lines(renderTable([["aaaaaa", "bb"]], { maxWidth: 8 })), ["aaa | bb", "aaa |   "]);
});

test("long words are broken and the last piece continues the line", () => {
  assert.deepEqual(lines(renderTable([["abcdefghij x y"]], { maxWidth: 4 })), ["abcd", "efgh", "ij x", "y   "]);
});

test("a long word after other words starts a new line", () => {
  assert.deepEqual(lines(renderTable([["ab abcdefg"]], { maxWidth: 4 })), ["ab  ", "abcd", "efg "]);
});

test("explicit newlines start paragraphs", () => {
  assert.deepEqual(lines(renderTable([["one\n\ntwo three", "x"]])), ["one       | x", "          |  ", "two three |  "]);
});

test("wide characters count as two columns", () => {
  assert.equal(renderTable([["日本", "ab"], ["x", "c"]]), "日本 | ab\nx    | c ");
});

test("astral wide characters are measured per code point", () => {
  assert.equal(renderTable([["𠀀x", "😀"], ["a", "b"]]), "𠀀x | 😀\na   | b ");
});

test("breaking wide words never splits a character", () => {
  assert.deepEqual(lines(renderTable([["日本語の", "a"]], { maxWidth: 6 })), ["日 | a", "本 |  ", "語 |  ", "の |  "]);
  assert.deepEqual(lines(renderTable([["日本語の", "a"]], { maxWidth: 7 })), ["日  | a", "本  |  ", "語  |  ", "の  |  "]);
  assert.deepEqual(lines(renderTable([["日本語", "a"]], { maxWidth: 9 })), ["日本  | a", "語    |  "]);
});

test("columns with wide characters have a minimum width of 2", () => {
  assert.deepEqual(lines(renderTable([["日本", "abc"]], { maxWidth: 6 })), ["日 | a", "本 | b", "   | c"]);
});

test("RangeError when the table cannot fit", () => {
  assert.throws(() => renderTable([["abc", "def"]], { maxWidth: 4 }), RangeError);
  assert.throws(() => renderTable([["日本", "abc"]], { maxWidth: 5 }), RangeError);
});

test("invalid options", () => {
  assert.throws(() => renderTable([["a"]], { maxWidth: 0 }), RangeError);
  assert.throws(() => renderTable([["a"]], { maxWidth: 2.5 }), RangeError);
  assert.throws(() => renderTable([["a"]], { align: ["middle" as never] }), RangeError);
});

test("packageReport uses the table", () => {
  const out = packageReport(
    [{ name: "left-pad", sizeBytes: 1536, downloads: 1234567, description: "pads strings on the left" }],
    44,
  );
  assert.deepEqual(lines(out), [
    "Package  |   Size | Downloads | Description ",
    "---------+--------+-----------+-------------",
    "left-pad | 1.5 KB | 1,234,567 | pads strings",
    "         |        |           | on the left ",
  ]);
});
