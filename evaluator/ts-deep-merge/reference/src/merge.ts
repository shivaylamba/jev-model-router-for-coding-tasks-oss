type PlainObject = Record<string, unknown>;
export type MergeOptions = { arrays?: "replace" | "concat" };

const SKIPPED = new Set(["__proto__", "constructor", "prototype"]);

function isPlainObject(value: unknown): value is PlainObject {
  if (value === null || typeof value !== "object") return false;
  const proto = Object.getPrototypeOf(value);
  return proto === Object.prototype || proto === null;
}

function copyValue(value: unknown): unknown {
  if (isPlainObject(value)) return copyPlain(value);
  if (Array.isArray(value)) return [...value];
  return value;
}

function copyPlain(source: PlainObject): PlainObject {
  const out: PlainObject = {};
  for (const key of Object.keys(source)) {
    if (SKIPPED.has(key)) continue;
    const value = source[key];
    if (value === undefined) continue;
    out[key] = copyValue(value);
  }
  return out;
}

function mergeInto(target: PlainObject, source: PlainObject, arrays: "replace" | "concat"): void {
  for (const key of Object.keys(source)) {
    if (SKIPPED.has(key)) continue;
    const value = source[key];
    if (value === undefined) continue;
    const current = Object.prototype.hasOwnProperty.call(target, key) ? target[key] : undefined;
    if (isPlainObject(value) && isPlainObject(current)) {
      mergeInto(current, value, arrays);
    } else if (arrays === "concat" && Array.isArray(value) && Array.isArray(current)) {
      target[key] = [...current, ...value];
    } else {
      target[key] = copyValue(value);
    }
  }
}

export function deepMergeWith(options: MergeOptions, target: unknown, ...sources: unknown[]): PlainObject {
  const arrays = options?.arrays ?? "replace";
  if (arrays !== "replace" && arrays !== "concat") {
    throw new RangeError(`unknown arrays option: ${String(arrays)}`);
  }
  if (!isPlainObject(target)) throw new TypeError("target must be a plain object");
  for (const source of sources) {
    if (source !== null && source !== undefined && !isPlainObject(source)) {
      throw new TypeError("sources must be plain objects");
    }
  }
  const result = copyPlain(target);
  for (const source of sources) {
    if (source === null || source === undefined) continue;
    mergeInto(result, source as PlainObject, arrays);
  }
  return result;
}

export function deepMerge(target: unknown, ...sources: unknown[]): PlainObject {
  return deepMergeWith({}, target, ...sources);
}
