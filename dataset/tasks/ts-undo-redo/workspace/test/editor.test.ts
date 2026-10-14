import { test } from "node:test";
import assert from "node:assert/strict";
import { Editor } from "../src/editor.ts";

test("starts with the cursor at the end", () => {
  const editor = new Editor("hello");
  assert.deepEqual(editor.selection, { start: 5, end: 5 });
});

test("insert replaces the selection", () => {
  const editor = new Editor("hello world");
  editor.select(6, 11);
  editor.insert("there");
  assert.equal(editor.text, "hello there");
  assert.deepEqual(editor.selection, { start: 11, end: 11 });
});

test("select clamps and orders", () => {
  const editor = new Editor("abc");
  editor.select(10, -2);
  assert.deepEqual(editor.selection, { start: 0, end: 3 });
});

test("deleteBackward and deleteForward", () => {
  const editor = new Editor("abcd");
  editor.select(2);
  editor.deleteBackward();
  assert.equal(editor.text, "acd");
  editor.deleteForward();
  assert.equal(editor.text, "ad");
  assert.deepEqual(editor.selection, { start: 1, end: 1 });
});
