import { test } from "node:test";
import assert from "node:assert/strict";
import { run } from "../src/cli.js";
import { count } from "../src/count.js";

function fakeIo(files) {
  const io = { out: "", err: "" };
  io.readFile = (path) => {
    if (!(path in files)) throw new Error("ENOENT");
    return files[path];
  };
  io.stdout = (text) => { io.out += text; };
  io.stderr = (text) => { io.err += text; };
  return io;
}

test("count", () => {
  assert.deepEqual(count("one two\nthree\n"), { lines: 2, words: 3, chars: 14 });
});

test("single file", () => {
  const io = fakeIo({ "a.txt": "hello world\n" });
  assert.equal(run(["a.txt"], io), 0);
  assert.equal(io.out, "      1       2      12 a.txt\n");
});

test("several files with a total and a missing file", () => {
  const io = fakeIo({ "a.txt": "a b\n", "b.txt": "c\n" });
  assert.equal(run(["a.txt", "nope.txt", "b.txt"], io), 1);
  assert.equal(io.out, "      1       2       4 a.txt\n      1       1       2 b.txt\n      2       3       6 total\n");
  assert.equal(io.err, "tally: cannot read nope.txt\n");
});

test("unknown option", () => {
  const io = fakeIo({});
  assert.equal(run(["-x"], io), 2);
  assert.equal(io.out, "");
});
