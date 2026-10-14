import { test } from "node:test";
import assert from "node:assert/strict";
import { validate } from "../src/validate.ts";
import { SchemaError } from "../src/types.ts";

type Err = { path: string; keyword: string };

function errs(schema: unknown, data: unknown): string[] {
  return (validate(schema as never, data as never) as Err[])
    .map((e) => `${e.path} ${e.keyword}`)
    .sort();
}

test("type, including integer and multiple names", () => {
  assert.deepEqual(errs({ type: "integer" }, 2.0), []);
  assert.deepEqual(errs({ type: "integer" }, 2.5), [" type"]);
  assert.deepEqual(errs({ type: "number" }, 7), []);
  assert.deepEqual(errs({ type: "object" }, []), [" type"]);
  assert.deepEqual(errs({ type: "object" }, null), [" type"]);
  assert.deepEqual(errs({ type: ["array", "boolean"] }, false), []);
});

test("enum and const use deep, type-strict equality", () => {
  assert.deepEqual(errs({ enum: ["a", 1, null] }, null), []);
  assert.deepEqual(errs({ enum: ["1", true] }, 1), [" enum"]);
  assert.deepEqual(errs({ enum: [{ a: 1, b: [1, 2] }] }, { b: [1, 2], a: 1 }), []);
  assert.deepEqual(errs({ enum: [{ a: 1, b: [1, 2] }] }, { a: 1, b: [2, 1] }), [" enum"]);
  assert.deepEqual(errs({ enum: [{ a: 1 }] }, { a: 1, b: 2 }), [" enum"]);
  assert.deepEqual(errs({ const: [1, { x: "y" }] }, [1, { x: "y" }]), []);
  assert.deepEqual(errs({ const: 0 }, false), [" const"]);
  assert.deepEqual(errs({ const: null }, null), []);
  assert.deepEqual(errs({ const: [] }, {}), [" const"]);
});

test("numeric bounds", () => {
  const schema = { minimum: 1, maximum: 10 };
  assert.deepEqual(errs(schema, 1), []);
  assert.deepEqual(errs(schema, 10), []);
  assert.deepEqual(errs(schema, 0.5), [" minimum"]);
  assert.deepEqual(errs(schema, 11), [" maximum"]);
  const exclusive = { exclusiveMinimum: 0, exclusiveMaximum: 1 };
  assert.deepEqual(errs(exclusive, 0), [" exclusiveMinimum"]);
  assert.deepEqual(errs(exclusive, 1), [" exclusiveMaximum"]);
  assert.deepEqual(errs(exclusive, 0.5), []);
});

test("string lengths count code points", () => {
  assert.deepEqual(errs({ maxLength: 2 }, "😀😀"), []);
  assert.deepEqual(errs({ maxLength: 1 }, "😀😀"), [" maxLength"]);
  assert.deepEqual(errs({ minLength: 2 }, "😀"), [" minLength"]);
  assert.deepEqual(errs({ minLength: 3, maxLength: 1 }, "ab"), [" maxLength", " minLength"]);
});

test("pattern is unanchored and unicode-aware", () => {
  assert.deepEqual(errs({ pattern: "[0-9]+" }, "abc123def"), []);
  assert.deepEqual(errs({ pattern: "^[0-9]+$" }, "abc123"), [" pattern"]);
  assert.deepEqual(errs({ pattern: "^\\p{Lu}" }, "Émile"), []);
  assert.deepEqual(errs({ pattern: "^.$" }, "😀"), []);
});

test("type-specific keywords ignore other types", () => {
  const schema = { minimum: 5, minLength: 5, pattern: "^x", required: ["a"], minItems: 3, uniqueItems: true, additionalProperties: false };
  assert.deepEqual(errs(schema, "xxxxx"), []);
  assert.deepEqual(errs(schema, 9), []);
  assert.deepEqual(errs(schema, null), []);
  assert.deepEqual(errs(schema, [1, 2, 3]), []);
});

test("keywords are independent", () => {
  assert.deepEqual(errs({ type: "string", enum: ["a"], minimum: 3 }, 2), [" enum", " minimum", " type"]);
});

test("required and properties keep working", () => {
  const schema = {
    type: "object",
    required: ["id", "name"],
    properties: { id: { type: "integer", minimum: 1 }, name: { type: "string", minLength: 1 } },
  };
  assert.deepEqual(errs(schema, { id: 0 }), ["/id minimum", "/name required"]);
});

test("additionalProperties false is relative to properties", () => {
  const schema = { properties: { a: {}, b: {} }, additionalProperties: false };
  assert.deepEqual(errs(schema, { a: 1, c: 2, d: 3 }), ["/c additionalProperties", "/d additionalProperties"]);
  assert.deepEqual(errs({ additionalProperties: false }, { x: 1 }), ["/x additionalProperties"]);
  assert.deepEqual(errs({ additionalProperties: false }, {}), []);
});

test("additionalProperties as a schema", () => {
  const schema = { properties: { name: { type: "string" } }, additionalProperties: { type: "number" } };
  assert.deepEqual(errs(schema, { name: "n", x: 1, y: "two" }), ["/y type"]);
  assert.deepEqual(errs(schema, { name: 5 }), ["/name type"]);
  assert.deepEqual(errs({ additionalProperties: true }, { anything: 1 }), []);
});

test("arrays: bounds, items and uniqueItems", () => {
  assert.deepEqual(errs({ minItems: 2 }, [1]), [" minItems"]);
  assert.deepEqual(errs({ maxItems: 1 }, [1, 2]), [" maxItems"]);
  assert.deepEqual(errs({ items: { type: "string" } }, ["a", 1, "b", null]), ["/1 type", "/3 type"]);
  assert.deepEqual(errs({ uniqueItems: true }, [1, 2, 1, 2, 1]), [" uniqueItems"]);
  assert.deepEqual(errs({ uniqueItems: true }, [{ a: 1, b: 2 }, { b: 2, a: 1 }]), [" uniqueItems"]);
  assert.deepEqual(errs({ uniqueItems: true }, [1, "1", true, [1], { "1": 1 }]), []);
  assert.deepEqual(errs({ uniqueItems: false }, [1, 1]), []);
});

test("JSON Pointer escaping", () => {
  const schema = { items: { properties: { "a/b": { type: "string" }, "c~d": { type: "string" } } } };
  assert.deepEqual(errs(schema, [{}, {}, { "a/b": 1, "c~d": 2 }]), ["/2/a~1b type", "/2/c~0d type"]);
  assert.deepEqual(errs({ required: ["x/y~z"] }, {}), ["/x~1y~0z required"]);
});

test("allOf merges errors from every subschema", () => {
  const schema = { allOf: [{ type: "string" }, { minimum: 3 }, { maximum: 1 }] };
  assert.deepEqual(errs(schema, 2), [" maximum", " minimum", " type"]);
  assert.deepEqual(errs({ allOf: [{ type: "object" }, { properties: { a: { type: "string" } } }] }, { a: 1 }), ["/a type"]);
});

test("no duplicate errors", () => {
  assert.deepEqual(errs({ type: "string", allOf: [{ type: "string" }, { type: "string" }] }, 1), [" type"]);
});

test("anyOf reports one error and hides subschema errors", () => {
  const schema = { properties: { v: { anyOf: [{ type: "string" }, { type: "integer", minimum: 10 }] } } };
  assert.deepEqual(errs(schema, { v: "x" }), []);
  assert.deepEqual(errs(schema, { v: 12 }), []);
  assert.deepEqual(errs(schema, { v: 5 }), ["/v anyOf"]);
  assert.deepEqual(errs({ anyOf: [{ required: ["a"] }, { required: ["b"] }] }, {}), [" anyOf"]);
});

test("oneOf needs exactly one match", () => {
  const schema = { oneOf: [{ type: "integer" }, { minimum: 0 }] };
  assert.deepEqual(errs(schema, -1), []);
  assert.deepEqual(errs(schema, 0.5), []);
  assert.deepEqual(errs(schema, 3), [" oneOf"]);
  assert.deepEqual(errs(schema, -0.5), [" oneOf"]);
  assert.deepEqual(errs({ items: { oneOf: [{ type: "string" }, { type: "null" }] } }, ["a", 1]), ["/1 oneOf"]);
});

test("$ref into definitions, with siblings", () => {
  const schema = {
    definitions: { positive: { type: "number", exclusiveMinimum: 0 } },
    properties: {
      price: { $ref: "#/definitions/positive", maximum: 100 },
    },
  };
  assert.deepEqual(errs(schema, { price: 50 }), []);
  assert.deepEqual(errs(schema, { price: 0 }), ["/price exclusiveMinimum"]);
  assert.deepEqual(errs(schema, { price: 101 }), ["/price maximum"]);
});

test("$ref with escaped tokens and array indexes", () => {
  const schema = {
    defs: { "a/b": { type: "string" }, "t~x": { type: "integer" }, list: [{ type: "boolean" }] },
    properties: {
      p: { $ref: "#/defs/a~1b" },
      q: { $ref: "#/defs/t~0x" },
      r: { $ref: "#/defs/list/0" },
    },
  };
  assert.deepEqual(errs(schema, { p: "s", q: 1, r: true }), []);
  assert.deepEqual(errs(schema, { p: 1, q: "1", r: 0 }), ["/p type", "/q type", "/r type"]);
});

test("recursive $ref", () => {
  const tree = {
    type: "object",
    required: ["value"],
    properties: {
      value: { type: "integer" },
      children: { type: "array", items: { $ref: "#" } },
    },
    additionalProperties: false,
  };
  const data = {
    value: 1,
    children: [{ value: 2 }, { value: 3, children: [{ value: "four", extra: true }, {}] }],
  };
  assert.deepEqual(errs(tree, data), [
    "/children/1/children/0/extra additionalProperties",
    "/children/1/children/0/value type",
    "/children/1/children/1/value required",
  ]);
});

test("unresolvable or non-local $ref throws SchemaError", () => {
  assert.throws(() => validate({ $ref: "#/definitions/missing" } as never, 1 as never), SchemaError);
  assert.throws(() => validate({ $ref: "other.json#/a" } as never, 1 as never), SchemaError);
  assert.throws(
    () => validate({ properties: { a: { $ref: "#/nope" } } } as never, { a: 1 } as never),
    SchemaError,
  );
});

test("false schemas inside keywords", () => {
  assert.deepEqual(errs({ properties: { gone: false } }, { gone: 1 }), ["/gone false"]);
  assert.deepEqual(errs({ items: false }, []), []);
  assert.deepEqual(errs({ items: false }, [1]), ["/0 false"]);
});

test("a realistic payload", () => {
  const schema = {
    $defs: { tag: { type: "string", pattern: "^[a-z-]+$", maxLength: 12 } },
    type: "object",
    required: ["event", "tags"],
    properties: {
      event: { enum: ["push", "release"] },
      tags: { type: "array", items: { $ref: "#/$defs/tag" }, uniqueItems: true, maxItems: 3 },
      meta: { type: "object", additionalProperties: { type: ["string", "number"] } },
    },
    additionalProperties: false,
  };
  assert.deepEqual(errs(schema, { event: "push", tags: ["a", "b-c"], meta: { n: 1, s: "x" } }), []);
  assert.deepEqual(
    errs(schema, { event: "pull", tags: ["ok", "Bad", "ok", "way-too-long-tag"], meta: { flag: true }, x: 1 }),
    [
      "/event enum",
      "/meta/flag type",
      "/tags maxItems",
      "/tags uniqueItems",
      "/tags/1 pattern",
      "/tags/3 maxLength",
      "/x additionalProperties",
    ],
  );
});
