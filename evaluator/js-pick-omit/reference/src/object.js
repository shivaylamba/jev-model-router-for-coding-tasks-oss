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

const own = (obj, key) => Object.prototype.propertyIsEnumerable.call(obj, key);

/**
 * A new object with only the listed keys that are own enumerable properties of `obj`,
 * in the order they appear in `keys`.
 * @param {object} obj
 * @param {string[]} keys
 */
export function pick(obj, keys) {
  const out = {};
  for (const key of keys) {
    if (own(obj, key)) out[key] = obj[key];
  }
  return out;
}

/**
 * A new object with every own enumerable string key of `obj` except the listed ones,
 * in the original order.
 * @param {object} obj
 * @param {string[]} keys
 */
export function omit(obj, keys) {
  const drop = new Set(keys);
  const out = {};
  for (const key of Object.keys(obj)) {
    if (!drop.has(key)) out[key] = obj[key];
  }
  return out;
}
