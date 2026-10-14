function channel(value: number): string {
  if (!Number.isInteger(value) || value < 0 || value > 255) {
    throw new RangeError(`colour channel out of range: ${value}`);
  }
  return value.toString(16).padStart(2, "0");
}

/** Format RGB channels (0-255) as a lowercase "#rrggbb" string. */
export function rgbToHex(r: number, g: number, b: number): string {
  return `#${channel(r)}${channel(g)}${channel(b)}`;
}

/**
 * Normalize "#rgb", "#rgba", "#rrggbb" or "#rrggbbaa" (any case, surrounding
 * whitespace ignored) to lowercase "#rrggbb" or "#rrggbbaa"; null if invalid.
 */
export function normalizeHexColor(input: string): string | null {
  if (typeof input !== "string") return null;
  const match = /^#([0-9a-f]{3}|[0-9a-f]{4}|[0-9a-f]{6}|[0-9a-f]{8})$/i.exec(input.trim());
  if (!match) return null;
  let digits = match[1].toLowerCase();
  if (digits.length <= 4) {
    digits = [...digits].map((d) => d + d).join("");
  }
  return `#${digits}`;
}
