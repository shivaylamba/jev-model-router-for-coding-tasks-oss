import { test } from "node:test";
import assert from "node:assert/strict";
import { validate } from "../src/validate.ts";

test("type", () => {
  assert.deepEqual(validate({ type: "string" }, "x"), []);
  assert.deepEqual(validate({ type: "string" }, 1), [{ path: "", keyword: "type" }]);
  assert.deepEqual(validate({ type: ["string", "null"] }, null), []);
});

test("required points at the missing member", () => {
  assert.deepEqual(validate({ type: "object", required: ["id"] }, {}), [{ path: "/id", keyword: "required" }]);
});

test("properties validate nested members", () => {
  const schema = { properties: { user: { properties: { age: { type: "integer" } } } } };
  assert.deepEqual(validate(schema, { user: { age: 1.5 } }), [{ path: "/user/age", keyword: "type" }]);
});

test("boolean schemas", () => {
  assert.deepEqual(validate(true, { anything: 1 }), []);
  assert.deepEqual(validate(false, 1), [{ path: "", keyword: "false" }]);
});
