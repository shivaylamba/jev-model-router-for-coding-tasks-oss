/**
 * True for objects created by `{}`, `Object.create(null)` or `new Object()`.
 * @param {unknown} value
 * @returns {boolean}
 */
export function isPlainObject(value) {
  if (value === null || typeof value !== "object") return false;
  const proto = Object.getPrototypeOf(value);
  return proto === null || proto === Object.prototype;
}

/**
 * A new object with the same own enumerable keys, each value passed through `fn(value, key)`.
 * @param {Record<string, unknown>} obj
 * @param {(value: unknown, key: string) => unknown} fn
 */
export function mapValues(obj, fn) {
  const out = {};
  for (const key of Object.keys(obj)) out[key] = fn(obj[key], key);
  return out;
}
