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
