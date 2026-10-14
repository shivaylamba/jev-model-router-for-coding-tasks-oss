/** Escape one JSON Pointer reference token. */
export function escapeToken(token: string): string {
  return token.replace(/~/g, "~0").replace(/\//g, "~1");
}

/** Append a member name or array index to a JSON Pointer. */
export function appendPointer(base: string, token: string | number): string {
  return `${base}/${escapeToken(String(token))}`;
}
