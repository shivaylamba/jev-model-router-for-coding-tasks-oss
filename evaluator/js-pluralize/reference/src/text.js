/**
 * Upper-case the first character.
 * @param {string} s
 */
export function capitalize(s) {
  return s.length === 0 ? s : s[0].toUpperCase() + s.slice(1);
}

/**
 * Shorten to at most `max` characters, ending with "…" when cut.
 * @param {string} s
 * @param {number} max
 */
export function truncate(s, max) {
  return s.length <= max ? s : s.slice(0, Math.max(0, max - 1)) + "…";
}

/**
 * "1 file", "3 files", "2 boxes", "4 cities". The singular is used only when count is exactly 1.
 * @param {number} count
 * @param {string} singular
 * @param {string} [plural]
 */
export function pluralize(count, singular, plural) {
  if (typeof count !== "number" || !Number.isFinite(count)) {
    throw new TypeError("count must be a finite number");
  }
  if (count === 1) return `${count} ${singular}`;
  return `${count} ${plural ?? defaultPlural(singular)}`;
}

function defaultPlural(word) {
  if (/(s|x|z|ch|sh)$/i.test(word)) return word + "es";
  if (/[^aeiou]y$/i.test(word)) return word.slice(0, -1) + "ies";
  return word + "s";
}
