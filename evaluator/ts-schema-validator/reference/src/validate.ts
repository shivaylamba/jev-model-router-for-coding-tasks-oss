import { appendPointer } from "./pointer.ts";
import { SchemaError } from "./types.ts";
import type { Json, Schema, SchemaObject, ValidationError } from "./types.ts";

function isPlainObject(value: unknown): value is { [key: string]: Json } {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function matchesType(value: Json, type: string): boolean {
  switch (type) {
    case "null":
      return value === null;
    case "boolean":
      return typeof value === "boolean";
    case "object":
      return isPlainObject(value);
    case "array":
      return Array.isArray(value);
    case "number":
      return typeof value === "number";
    case "integer":
      return typeof value === "number" && Number.isInteger(value);
    case "string":
      return typeof value === "string";
    default:
      return false;
  }
}

export function deepEqual(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (Array.isArray(a) || Array.isArray(b)) {
    if (!Array.isArray(a) || !Array.isArray(b) || a.length !== b.length) return false;
    return a.every((item, index) => deepEqual(item, b[index]));
  }
  if (isPlainObject(a) && isPlainObject(b)) {
    const keysA = Object.keys(a);
    if (keysA.length !== Object.keys(b).length) return false;
    return keysA.every((key) => Object.hasOwn(b, key) && deepEqual(a[key], b[key]));
  }
  return false;
}

function decodeToken(token: string): string {
  return token.replace(/~1/g, "/").replace(/~0/g, "~");
}

function resolveRef(root: Schema, ref: string): Schema {
  if (ref === "#") return root;
  if (!ref.startsWith("#/")) throw new SchemaError(`unsupported $ref ${ref}`);
  let current: unknown = root;
  for (const raw of ref.slice(2).split("/")) {
    const token = decodeToken(raw);
    if (Array.isArray(current) && /^(0|[1-9]\d*)$/.test(token) && Number(token) < current.length) {
      current = current[Number(token)];
    } else if (isPlainObject(current) && Object.hasOwn(current, token)) {
      current = current[token];
    } else {
      throw new SchemaError(`unresolvable $ref ${ref}`);
    }
  }
  if (typeof current !== "boolean" && !isPlainObject(current)) {
    throw new SchemaError(`$ref ${ref} does not point to a schema`);
  }
  return current as Schema;
}

class Collector {
  readonly errors: ValidationError[] = [];
  private readonly seen = new Set<string>();

  add(path: string, keyword: string): void {
    const key = `${keyword}\u0000${path}`;
    if (this.seen.has(key)) return;
    this.seen.add(key);
    this.errors.push({ path, keyword });
  }
}

function codePointLength(text: string): number {
  let count = 0;
  for (const _ of text) count++;
  return count;
}

function isValid(root: Schema, schema: Schema, value: Json, path: string): boolean {
  const sub = new Collector();
  check(root, schema, value, path, sub);
  return sub.errors.length === 0;
}

function check(root: Schema, schema: Schema, value: Json, path: string, out: Collector): void {
  if (schema === true) return;
  if (schema === false) {
    out.add(path, "false");
    return;
  }
  const s = schema as SchemaObject;

  if (typeof s.$ref === "string") {
    check(root, resolveRef(root, s.$ref), value, path, out);
  }

  if (s.type !== undefined) {
    const types = Array.isArray(s.type) ? (s.type as string[]) : [s.type as string];
    if (!types.some((t) => matchesType(value, t))) out.add(path, "type");
  }
  if (Array.isArray(s.enum) && !s.enum.some((candidate) => deepEqual(candidate, value))) {
    out.add(path, "enum");
  }
  if (Object.hasOwn(s, "const") && !deepEqual(s.const, value)) {
    out.add(path, "const");
  }

  if (typeof value === "number") {
    if (typeof s.minimum === "number" && value < s.minimum) out.add(path, "minimum");
    if (typeof s.maximum === "number" && value > s.maximum) out.add(path, "maximum");
    if (typeof s.exclusiveMinimum === "number" && value <= s.exclusiveMinimum) out.add(path, "exclusiveMinimum");
    if (typeof s.exclusiveMaximum === "number" && value >= s.exclusiveMaximum) out.add(path, "exclusiveMaximum");
  }

  if (typeof value === "string") {
    const length = codePointLength(value);
    if (typeof s.minLength === "number" && length < s.minLength) out.add(path, "minLength");
    if (typeof s.maxLength === "number" && length > s.maxLength) out.add(path, "maxLength");
    if (typeof s.pattern === "string" && !new RegExp(s.pattern, "u").test(value)) out.add(path, "pattern");
  }

  if (isPlainObject(value)) {
    if (Array.isArray(s.required)) {
      for (const name of s.required as string[]) {
        if (!Object.hasOwn(value, name)) out.add(appendPointer(path, name), "required");
      }
    }
    const properties = isPlainObject(s.properties) ? (s.properties as { [key: string]: Schema }) : {};
    for (const [name, sub] of Object.entries(properties)) {
      if (Object.hasOwn(value, name)) check(root, sub, value[name], appendPointer(path, name), out);
    }
    if (s.additionalProperties !== undefined && s.additionalProperties !== true) {
      for (const name of Object.keys(value)) {
        if (Object.hasOwn(properties, name)) continue;
        const memberPath = appendPointer(path, name);
        if (s.additionalProperties === false) {
          out.add(memberPath, "additionalProperties");
        } else {
          check(root, s.additionalProperties as Schema, value[name], memberPath, out);
        }
      }
    }
  }

  if (Array.isArray(value)) {
    if (typeof s.minItems === "number" && value.length < s.minItems) out.add(path, "minItems");
    if (typeof s.maxItems === "number" && value.length > s.maxItems) out.add(path, "maxItems");
    if (s.items !== undefined) {
      value.forEach((item, index) => check(root, s.items as Schema, item, appendPointer(path, index), out));
    }
    if (s.uniqueItems === true) {
      outer: for (let i = 0; i < value.length; i++) {
        for (let j = i + 1; j < value.length; j++) {
          if (deepEqual(value[i], value[j])) {
            out.add(path, "uniqueItems");
            break outer;
          }
        }
      }
    }
  }

  if (Array.isArray(s.allOf)) {
    for (const sub of s.allOf as Schema[]) check(root, sub, value, path, out);
  }
  if (Array.isArray(s.anyOf)) {
    if (!(s.anyOf as Schema[]).some((sub) => isValid(root, sub, value, path))) out.add(path, "anyOf");
  }
  if (Array.isArray(s.oneOf)) {
    const matches = (s.oneOf as Schema[]).filter((sub) => isValid(root, sub, value, path)).length;
    if (matches !== 1) out.add(path, "oneOf");
  }
}

export function validate(schema: Schema, data: Json): ValidationError[] {
  const out = new Collector();
  check(schema, schema, data, "", out);
  return out.errors;
}
