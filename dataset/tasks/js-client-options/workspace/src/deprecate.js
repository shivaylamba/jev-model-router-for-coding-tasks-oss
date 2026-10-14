/**
 * Deprecation warnings, reported at most once per code per process.
 *
 * By default warnings go to process.emitWarning with type "DeprecationWarning".
 * Tests can install their own handler and reset the "already warned" set.
 */

const defaultHandler = (code, message) => {
  process.emitWarning(message, { type: "DeprecationWarning", code });
};

let handler = defaultHandler;
const warned = new Set();

export function deprecate(code, message) {
  if (warned.has(code)) return;
  warned.add(code);
  handler(code, message);
}

/** Replace the handler (pass nothing to restore the default). */
export function setDeprecationHandler(fn = defaultHandler) {
  handler = fn;
}

/** Forget which codes have already warned. */
export function resetDeprecations() {
  warned.clear();
}
