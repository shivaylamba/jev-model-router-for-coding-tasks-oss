import { test } from "node:test";
import assert from "node:assert/strict";
import { run } from "../src/cli.js";

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

test("--json with one file", () => {
  const io = fakeIo({ "a.txt": "hello world\n" });
  assert.equal(run(["--json", "a.txt"], io), 0);
  assert.ok(io.out.endsWith("\n"));
  assert.deepEqual(JSON.parse(io.out), {
    files: [{ path: "a.txt", lines: 1, words: 2, chars: 12 }],
    total: { lines: 1, words: 2, chars: 12 },
  });
  assert.equal(io.err, "");
});

test("--json anywhere among the arguments, files in order", () => {
  const io = fakeIo({ "a.txt": "a b\n", "b.txt": "c\n" });
  assert.equal(run(["a.txt", "--json", "b.txt"], io), 0);
  assert.deepEqual(JSON.parse(io.out), {
    files: [
      { path: "a.txt", lines: 1, words: 2, chars: 4 },
      { path: "b.txt", lines: 1, words: 1, chars: 2 },
    ],
    total: { lines: 2, words: 3, chars: 6 },
  });
});

test("--json with an unreadable file", () => {
  const io = fakeIo({ "a.txt": "x\n" });
  assert.equal(run(["--json", "a.txt", "missing.txt"], io), 1);
  assert.deepEqual(JSON.parse(io.out).files.map((f) => f.path), ["a.txt"]);
  assert.equal(io.err, "tally: cannot read missing.txt\n");
});

test("--json with no files", () => {
  const io = fakeIo({});
  assert.equal(run(["--json"], io), 0);
  assert.deepEqual(JSON.parse(io.out), { files: [], total: { lines: 0, words: 0, chars: 0 } });
});

test("unknown options are still rejected", () => {
  const io = fakeIo({ "a.txt": "x" });
  assert.equal(run(["--json", "--yaml", "a.txt"], io), 2);
  assert.equal(io.out, "");
});

test("text output is unchanged without --json", () => {
  const io = fakeIo({ "a.txt": "hello world\n" });
  assert.equal(run(["a.txt"], io), 0);
  assert.equal(io.out, "      1       2      12 a.txt\n");
});
