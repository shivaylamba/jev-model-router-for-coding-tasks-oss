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
