import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { ConfigError, readConfig, type Config } from "../src/config.ts";

const dir = mkdtempSync(join(tmpdir(), "cfg-accept-"));
let counter = 0;
function fileWith(text: string): string {
  const path = join(dir, `config-${counter++}.json`);
  writeFileSync(path, text);
  return path;
}
const missing = join(dir, "does-not-exist.json");

function viaCallback(path: string): Promise<{ calls: Array<[Error | null, Config | undefined]>; returned: unknown }> {
  return new Promise((resolve) => {
    const calls: Array<[Error | null, Config | undefined]> = [];
    const returned = readConfig(path, (err, config) => {
      calls.push([err, config]);
      // Give a second (wrong) call a chance to happen before reporting.
      setImmediate(() => resolve({ calls, returned }));
    });
  });
}

test("returns a promise when no callback is given", async () => {
  const result = readConfig(fileWith('{"host": "0.0.0.0"}'));
  assert.ok(result instanceof Promise);
  assert.deepEqual(await result, { host: "0.0.0.0", port: 8080, debug: false });
});

test("promise resolves with all fields from the file", async () => {
  const config = await readConfig(fileWith('{"host": "dev.local", "port": 9000, "debug": true}'));
  assert.deepEqual(config, { host: "dev.local", port: 9000, debug: true });
});

test("promise rejects with the file-system error for a missing file", async () => {
  await assert.rejects(readConfig(missing), (err: NodeJS.ErrnoException) => err.code === "ENOENT");
});

test("promise rejects with SyntaxError for malformed JSON", async () => {
  await assert.rejects(readConfig(fileWith("{port: 1}")), SyntaxError);
});

test("promise rejects with ConfigError for bad values", async () => {
  await assert.rejects(readConfig(fileWith('{"port": 70000}')), ConfigError);
  await assert.rejects(readConfig(fileWith("[]")), ConfigError);
});

test("callback style still works and returns nothing", async () => {
  const { calls, returned } = await viaCallback(fileWith('{"port": 3000}'));
  assert.equal(returned, undefined);
  assert.equal(calls.length, 1);
  assert.equal(calls[0][0], null);
  assert.deepEqual(calls[0][1], { host: "localhost", port: 3000, debug: false });
});

test("callback receives errors exactly once and nothing is returned", async () => {
  const missingResult = await viaCallback(missing);
  assert.equal(missingResult.returned, undefined);
  assert.equal(missingResult.calls.length, 1);
  assert.equal((missingResult.calls[0][0] as NodeJS.ErrnoException).code, "ENOENT");

  const syntax = await viaCallback(fileWith("not json"));
  assert.equal(syntax.calls.length, 1);
  assert.ok(syntax.calls[0][0] instanceof SyntaxError);

  const bad = await viaCallback(fileWith('{"debug": "yes"}'));
  assert.equal(bad.calls.length, 1);
  assert.ok(bad.calls[0][0] instanceof ConfigError);
});
