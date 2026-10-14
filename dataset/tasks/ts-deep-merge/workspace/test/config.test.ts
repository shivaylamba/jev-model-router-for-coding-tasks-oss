import { test } from "node:test";
import assert from "node:assert/strict";
import { DEFAULTS, loadConfig } from "../src/config.ts";

test("no layers gives the defaults", () => {
  assert.deepEqual(loadConfig(), DEFAULTS);
});

test("a top-level value is overridden", () => {
  assert.deepEqual(loadConfig({ features: ["tracing"] }).features, ["tracing"]);
});
