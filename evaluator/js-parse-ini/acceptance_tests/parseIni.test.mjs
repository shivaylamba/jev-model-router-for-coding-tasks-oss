import { test } from "node:test";
import assert from "node:assert/strict";
import { parseIni, stringifyIni } from "../src/ini.js";

function syntaxErrorAt(text, line) {
  assert.throws(() => parseIni(text), (error) => {
    assert.ok(error instanceof SyntaxError, `expected SyntaxError, got ${error}`);
    assert.equal(error.line, line);
    return true;
  });
}

test("sections, keys and trimming", () => {
  const text = "[server]\n  host =  example.com  \nport=8080\n\n[db]\nname = app\n";
  assert.deepEqual(parseIni(text), { server: { host: "example.com", port: "8080" }, db: { name: "app" } });
});

test("global keys go to the empty section, which is omitted when empty", () => {
  assert.deepEqual(parseIni("name = api\n[s]\na = 1\n"), { "": { name: "api" }, s: { a: "1" } });
  assert.deepEqual(Object.keys(parseIni("[s]\na = 1\n")), ["s"]);
});

test("comments and blank lines; no inline comments", () => {
  const text = "; top\n# also\n[s]\n   ; indented comment\nurl = http://x/#frag ; not a comment\n";
  assert.deepEqual(parseIni(text), { s: { url: "http://x/#frag ; not a comment" } });
});

test("section names are kept literally and empty sections appear", () => {
  assert.deepEqual(parseIni("[ server.http ]\n[empty]\n"), { "server.http": {}, empty: {} });
});

test("first = splits; empty values allowed", () => {
  assert.deepEqual(parseIni("[s]\nquery = a=1&b=2\nblank =\n"), { s: { query: "a=1&b=2", blank: "" } });
});

test("duplicate sections merge and last key wins, in first-appearance order", () => {
  const text = "[a]\nx = 1\ny = 2\n[b]\nz = 3\n[a]\nx = 9\nw = 4\n";
  const result = parseIni(text);
  assert.deepEqual(result, { a: { x: "9", y: "2", w: "4" }, b: { z: "3" } });
  assert.deepEqual(Object.keys(result), ["a", "b"]);
});

test("quoted values keep whitespace and decode escapes", () => {
  const text = '[s]\nmotd = "  hello \\"world\\"  "\npath = "C:\\\\tmp\\tx\\ny"\nsemi = "a ; b"   \n';
  assert.deepEqual(parseIni(text), { s: { motd: '  hello "world"  ', path: "C:\\tmp\tx\ny", semi: "a ; b" } });
});

test("line continuation joins with a single space", () => {
  const text = "[s]\nlist = one,   \\\n     two, \\\n  [three]\nafter = x\n";
  assert.deepEqual(parseIni(text), { s: { list: "one, two, [three]", after: "x" } });
});

test("CRLF line endings", () => {
  assert.deepEqual(parseIni("[s]\r\na = 1\r\nb = \"q\"\r\n"), { s: { a: "1", b: "q" } });
});

test("round trip with stringifyIni", () => {
  const data = { "": { name: "api" }, s: { motd: ' padded "quoted" ', tab: "a\tb", plain: "x=y" } };
  assert.deepEqual(parseIni(stringifyIni(data)), data);
});

test("syntax errors carry the line number", () => {
  syntaxErrorAt("[s]\na = 1\njust text\n", 3);
  syntaxErrorAt("\n[s\n", 2);
  syntaxErrorAt("[s]\n[  ]\n", 2);
  syntaxErrorAt("[s]\n = value\n", 2);
  syntaxErrorAt('[s]\n\na = "open\n', 3);
  syntaxErrorAt('[s]\na = "bad \\q escape"\n', 2);
  syntaxErrorAt('[s]\na = "done" trailing\n', 2);
  syntaxErrorAt("[s]\r\nok = 1\r\nbroken\r\n", 3);
});

test("continuation on the last line is an error at that line", () => {
  syntaxErrorAt("[s]\na = one \\", 2);
  syntaxErrorAt("[s]\na = one \\\ntwo \\", 3);
});
