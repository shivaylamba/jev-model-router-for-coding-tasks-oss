import { test } from "node:test";
import assert from "node:assert/strict";
import { compareVersions, parseVersion } from "../src/semver.ts";

test("parseVersion", () => {
  assert.deepEqual(parseVersion("v1.20.3"), { major: 1, minor: 20, patch: 3 });
  assert.throws(() => parseVersion("1.2"), TypeError);
  assert.throws(() => parseVersion("1.2.3-rc.1"), TypeError);
  assert.throws(() => parseVersion("01.2.3"), TypeError);
});

test("compareVersions", () => {
  assert.ok(compareVersions("1.10.0", "1.9.9") > 0);
  assert.equal(compareVersions("2.0.0", "v2.0.0"), 0);
});
