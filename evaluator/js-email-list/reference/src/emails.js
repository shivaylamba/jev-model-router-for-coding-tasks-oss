const LOCAL = /^[A-Za-z0-9._%+-]{1,64}$/;
const LABEL = /^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$/;
const TLD = /^[A-Za-z]{2,}$/;

/** Whether a single address passes the rules in parseEmailList. */
export function isValidEmail(address) {
  const parts = address.split("@");
  if (parts.length !== 2) return false;
  const [local, domain] = parts;
  if (!LOCAL.test(local) || local.startsWith(".") || local.endsWith(".") || local.includes("..")) return false;
  const labels = domain.split(".");
  if (labels.length < 2) return false;
  if (!labels.every((label) => LABEL.test(label))) return false;
  return TLD.test(labels[labels.length - 1]);
}

/**
 * Split pasted text into valid and invalid addresses.
 * @param {string} text
 * @returns {{ valid: string[], invalid: string[] }}
 */
export function parseEmailList(text) {
  const valid = [];
  const invalid = [];
  const seen = new Set();
  for (const token of text.split(/[\s,;]+/)) {
    if (token === "") continue;
    if (!isValidEmail(token)) {
      invalid.push(token);
      continue;
    }
    const key = token.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    valid.push(token);
  }
  return { valid, invalid };
}
