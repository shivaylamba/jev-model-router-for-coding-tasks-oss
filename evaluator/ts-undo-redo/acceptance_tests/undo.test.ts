import { test } from "node:test";
import assert from "node:assert/strict";
import { Editor } from "../src/editor.ts";

function fakeClock(start = 0) {
  let now = start;
  return {
    clock: () => now,
    advance(ms: number) {
      now += ms;
    },
  };
}

function typeText(editor: Editor, text: string, time?: ReturnType<typeof fakeClock>, gap = 100) {
  for (const ch of text) {
    editor.insert(ch);
    time?.advance(gap);
  }
}

test("nothing to undo or redo at first", () => {
  const editor = new Editor("start", { clock: fakeClock().clock });
  assert.equal(editor.canUndo(), false);
  assert.equal(editor.canRedo(), false);
  assert.equal(editor.undo(), false);
  assert.equal(editor.redo(), false);
  assert.equal(editor.text, "start");
});

test("undo and redo restore text and selection", () => {
  const editor = new Editor("hello world", { clock: fakeClock().clock });
  editor.select(6, 11);
  editor.insert("there");
  assert.equal(editor.undo(), true);
  assert.equal(editor.text, "hello world");
  assert.deepEqual(editor.selection, { start: 6, end: 11 });
  assert.equal(editor.canRedo(), true);
  assert.equal(editor.redo(), true);
  assert.equal(editor.text, "hello there");
  assert.deepEqual(editor.selection, { start: 11, end: 11 });
});

test("typing within a second of each keystroke is one step", () => {
  const time = fakeClock();
  const editor = new Editor("", { clock: time.clock });
  typeText(editor, "hello", time, 900);
  assert.equal(editor.text, "hello");
  editor.undo();
  assert.equal(editor.text, "");
  assert.deepEqual(editor.selection, { start: 0, end: 0 });
  assert.equal(editor.canUndo(), false);
  editor.redo();
  assert.equal(editor.text, "hello");
  assert.deepEqual(editor.selection, { start: 5, end: 5 });
});

test("the 1000 ms boundary", () => {
  const time = fakeClock();
  const editor = new Editor("", { clock: time.clock });
  editor.insert("a");
  time.advance(999);
  editor.insert("b");
  time.advance(1000);
  editor.insert("c");
  editor.undo();
  assert.equal(editor.text, "ab");
  editor.undo();
  assert.equal(editor.text, "");
});

test("the gap is measured from the previous keystroke", () => {
  const time = fakeClock();
  const editor = new Editor("", { clock: time.clock });
  typeText(editor, "abcdefgh", time, 600);
  editor.undo();
  assert.equal(editor.text, "");
});

test("newlines and pastes are their own steps", () => {
  const time = fakeClock();
  const editor = new Editor("", { clock: time.clock });
  typeText(editor, "ab", time);
  editor.insert("\n");
  time.advance(10);
  typeText(editor, "cd", time);
  editor.insert("PASTE");
  time.advance(10);
  editor.insert("e");
  assert.equal(editor.text, "ab\ncdPASTEe");
  editor.undo();
  assert.equal(editor.text, "ab\ncdPASTE");
  editor.undo();
  assert.equal(editor.text, "ab\ncd");
  editor.undo();
  assert.equal(editor.text, "ab\n");
  editor.undo();
  assert.equal(editor.text, "ab");
});

test("replacing a selection with one character is its own step", () => {
  const time = fakeClock();
  const editor = new Editor("", { clock: time.clock });
  typeText(editor, "abc", time);
  editor.select(1, 2);
  editor.insert("X");
  time.advance(10);
  editor.insert("Y");
  assert.equal(editor.text, "aXYc");
  editor.undo();
  assert.equal(editor.text, "aXc");
  editor.undo();
  assert.equal(editor.text, "abc");
  assert.deepEqual(editor.selection, { start: 1, end: 2 });
});

test("select closes the typing group, even at the same position", () => {
  const time = fakeClock();
  const editor = new Editor("", { clock: time.clock });
  typeText(editor, "ab", time);
  editor.select(2);
  typeText(editor, "cd", time);
  editor.undo();
  assert.equal(editor.text, "ab");
});

test("a no-op delete closes the typing group", () => {
  const time = fakeClock();
  const editor = new Editor("", { clock: time.clock });
  typeText(editor, "ab", time);
  editor.deleteForward();
  typeText(editor, "cd", time);
  editor.undo();
  assert.equal(editor.text, "ab");
});

test("deletes are separate steps and restore the selection", () => {
  const editor = new Editor("abcdef", { clock: fakeClock().clock });
  editor.deleteBackward();
  editor.deleteBackward();
  editor.select(0);
  editor.deleteForward();
  assert.equal(editor.text, "bcd");
  editor.undo();
  assert.equal(editor.text, "abcd");
  assert.deepEqual(editor.selection, { start: 0, end: 0 });
  editor.undo();
  assert.equal(editor.text, "abcde");
  assert.deepEqual(editor.selection, { start: 5, end: 5 });
  editor.select(1, 3);
  editor.deleteBackward();
  editor.undo();
  assert.deepEqual(editor.selection, { start: 1, end: 3 });
});

test("no-op edits create no step and keep redo", () => {
  const editor = new Editor("x", { clock: fakeClock().clock });
  editor.select(0);
  editor.deleteBackward();
  editor.insert("");
  assert.equal(editor.canUndo(), false);
  editor.insert("y");
  editor.undo();
  assert.equal(editor.canRedo(), true);
  editor.select(0);
  editor.deleteBackward();
  editor.insert("");
  assert.equal(editor.canRedo(), true);
  editor.redo();
  assert.equal(editor.text, "yx");
});

test("insert of an empty string over a selection is a step", () => {
  const editor = new Editor("abc", { clock: fakeClock().clock });
  editor.select(0, 2);
  editor.insert("");
  assert.equal(editor.text, "c");
  editor.undo();
  assert.equal(editor.text, "abc");
});

test("a new change clears redo", () => {
  const time = fakeClock();
  const editor = new Editor("", { clock: time.clock });
  typeText(editor, "ab", time);
  editor.undo();
  editor.insert("z");
  assert.equal(editor.canRedo(), false);
  assert.equal(editor.redo(), false);
  assert.equal(editor.text, "z");
});

test("undo closes the group: typing after undo is a new step", () => {
  const time = fakeClock();
  const editor = new Editor("", { clock: time.clock });
  typeText(editor, "ab", time);
  time.advance(2000);
  typeText(editor, "cd", time);
  editor.undo();
  typeText(editor, "x", time);
  editor.undo();
  assert.equal(editor.text, "ab");
  editor.undo();
  assert.equal(editor.text, "");
});

test("redo closes the group", () => {
  const time = fakeClock();
  const editor = new Editor("", { clock: time.clock });
  typeText(editor, "ab", time);
  editor.undo();
  editor.redo();
  typeText(editor, "c", time);
  editor.undo();
  assert.equal(editor.text, "ab");
});

test("transactions are one step with before and after selection", () => {
  const editor = new Editor("one two", { clock: fakeClock().clock });
  editor.select(0, 3);
  const result = editor.transact(() => {
    editor.insert("ONE");
    editor.select(4, 7);
    editor.insert("TWO");
    editor.select(0);
    return 42;
  });
  assert.equal(result, 42);
  assert.equal(editor.text, "ONE TWO");
  editor.undo();
  assert.equal(editor.text, "one two");
  assert.deepEqual(editor.selection, { start: 0, end: 3 });
  assert.equal(editor.canUndo(), false);
  editor.redo();
  assert.equal(editor.text, "ONE TWO");
  assert.deepEqual(editor.selection, { start: 0, end: 0 });
});

test("nested transactions join the outer one", () => {
  const editor = new Editor("", { clock: fakeClock().clock });
  editor.transact(() => {
    editor.insert("a");
    editor.transact(() => {
      editor.insert("b");
    });
    editor.insert("c");
  });
  assert.equal(editor.text, "abc");
  editor.undo();
  assert.equal(editor.text, "");
  assert.equal(editor.canUndo(), false);
});

test("a transaction with no net change creates no step", () => {
  const editor = new Editor("abc", { clock: fakeClock().clock });
  editor.insert("d");
  editor.undo();
  editor.transact(() => {
    editor.insert("x");
    editor.deleteBackward();
  });
  assert.equal(editor.canUndo(), false);
  assert.equal(editor.canRedo(), true);
});

test("a failing transaction rolls back and rethrows", () => {
  const editor = new Editor("abc", { clock: fakeClock().clock });
  editor.insert("d");
  editor.undo();
  editor.select(1);
  const boom = new Error("boom");
  assert.throws(
    () =>
      editor.transact(() => {
        editor.insert("XYZ");
        editor.select(0, 2);
        throw boom;
      }),
    (error: unknown) => error === boom,
  );
  assert.equal(editor.text, "abc");
  assert.deepEqual(editor.selection, { start: 1, end: 1 });
  assert.equal(editor.canUndo(), false);
  assert.equal(editor.canRedo(), true);
});

test("a failing inner transaction rolls back only its own changes", () => {
  const editor = new Editor("", { clock: fakeClock().clock });
  editor.transact(() => {
    editor.insert("keep");
    try {
      editor.transact(() => {
        editor.insert("-drop");
        throw new Error("inner");
      });
    } catch {
      // ignored
    }
    editor.insert("!");
  });
  assert.equal(editor.text, "keep!");
  editor.undo();
  assert.equal(editor.text, "");
});

test("undo and redo inside a transaction throw", () => {
  const editor = new Editor("", { clock: fakeClock().clock });
  editor.insert("a");
  assert.throws(() => editor.transact(() => editor.undo()), Error);
  assert.throws(() => editor.transact(() => editor.redo()), Error);
  assert.equal(editor.text, "a");
});

test("typing does not merge across a transaction", () => {
  const time = fakeClock();
  const editor = new Editor("", { clock: time.clock });
  typeText(editor, "ab", time);
  editor.transact(() => typeText(editor, "cd", time));
  typeText(editor, "ef", time);
  assert.equal(editor.text, "abcdef");
  editor.undo();
  assert.equal(editor.text, "abcd");
  editor.undo();
  assert.equal(editor.text, "ab");
  editor.undo();
  assert.equal(editor.text, "");
});

test("history limit discards the oldest steps", () => {
  const editor = new Editor("", { clock: fakeClock().clock, historyLimit: 2 });
  editor.insert("one ");
  editor.insert("two ");
  editor.insert("three");
  assert.equal(editor.undo(), true);
  assert.equal(editor.undo(), true);
  assert.equal(editor.undo(), false);
  assert.equal(editor.text, "one ");
});

test("extending a typing group does not count against the limit", () => {
  const time = fakeClock();
  const editor = new Editor("", { clock: time.clock, historyLimit: 2 });
  editor.insert("X");
  time.advance(5000);
  typeText(editor, "abcdef", time);
  editor.undo();
  assert.equal(editor.text, "X");
  editor.undo();
  assert.equal(editor.text, "");
});

test("history limit 0 keeps nothing", () => {
  const editor = new Editor("", { clock: fakeClock().clock, historyLimit: 0 });
  editor.insert("abc");
  assert.equal(editor.canUndo(), false);
  assert.equal(editor.undo(), false);
  assert.equal(editor.text, "abc");
});

test("invalid history limits", () => {
  assert.throws(() => new Editor("", { historyLimit: -1 }), RangeError);
  assert.throws(() => new Editor("", { historyLimit: 1.5 }), RangeError);
});

test("default limit is 100", () => {
  const editor = new Editor("");
  for (let i = 0; i < 105; i++) editor.insert(`${i},`);
  let undone = 0;
  while (editor.undo()) undone++;
  assert.equal(undone, 100);
  assert.equal(editor.text, "0,1,2,3,4,");
});
