import { test } from "node:test";
import assert from "node:assert/strict";
import { stringifyIni } from "../src/ini.js";

test("writes global keys first, then sections", () => {
  const text = stringifyIni({ server: { port: 8080 }, "": { name: "api" } });
  assert.equal(text, "name = api\n\n[server]\nport = 8080\n");
});

test("quotes values that need it", () => {
  const text = stringifyIni({ s: { motd: ' hi "there"' } });
  assert.equal(text, '[s]\nmotd = " hi \\"there\\""\n');
});
