import { appendPointer } from "./pointer.ts";
import type { Json, Schema, SchemaObject, ValidationError } from "./types.ts";

// First version: supports `type`, `required` and `properties` only.
// See SPEC.md for the full set of keywords we need.

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

function check(schema: Schema, value: Json, path: string, errors: ValidationError[]): void {
  if (schema === true) return;
  if (schema === false) {
    errors.push({ path, keyword: "false" });
    return;
  }
  const s = schema as SchemaObject;

  if (s.type !== undefined) {
    const types = Array.isArray(s.type) ? (s.type as string[]) : [s.type as string];
    if (!types.some((t) => matchesType(value, t))) errors.push({ path, keyword: "type" });
  }

  if (isPlainObject(value)) {
    if (Array.isArray(s.required)) {
      for (const name of s.required as string[]) {
        if (!Object.hasOwn(value, name)) errors.push({ path: appendPointer(path, name), keyword: "required" });
      }
    }
    if (isPlainObject(s.properties)) {
      const properties = s.properties as { [key: string]: Schema };
      for (const [name, sub] of Object.entries(properties)) {
        if (Object.hasOwn(value, name)) check(sub, value[name], appendPointer(path, name), errors);
      }
    }
  }
}

export function validate(schema: Schema, data: Json): ValidationError[] {
  const errors: ValidationError[] = [];
  check(schema, data, "", errors);
  return errors;
}
