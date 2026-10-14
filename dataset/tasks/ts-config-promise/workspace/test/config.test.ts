import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { ConfigError, readConfig } from "../src/config.ts";

function fileWith(text: string): string {
  const dir = mkdtempSync(join(tmpdir(), "cfg-"));
  const path = join(dir, "devserver.json");
  writeFileSync(path, text);
  return path;
}

test("callback receives the merged config", (_t, done) => {
  readConfig(fileWith('{"port": 3000}'), (err, config) => {
    assert.equal(err, null);
    assert.deepEqual(config, { host: "localhost", port: 3000, debug: false });
    done();
  });
});

test("callback receives a ConfigError for a bad port", (_t, done) => {
  readConfig(fileWith('{"port": 0}'), (err) => {
    assert.ok(err instanceof ConfigError);
    done();
  });
});
