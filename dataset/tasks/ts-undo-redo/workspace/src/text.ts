/** A selection in UTF-16 code unit offsets, always with start <= end. Empty when start === end (a cursor). */
export interface Selection {
  start: number;
  end: number;
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/** Clamp both ends into [0, length] and order them. */
export function normalizeSelection(length: number, a: number, b: number): Selection {
  const x = clamp(Math.trunc(a), 0, length);
  const y = clamp(Math.trunc(b), 0, length);
  return x <= y ? { start: x, end: y } : { start: y, end: x };
}

/** Replace text[start, end) with `insert`. */
export function replaceRange(text: string, start: number, end: number, insert: string): string {
  return text.slice(0, start) + insert + text.slice(end);
}

export function isEmpty(selection: Selection): boolean {
  return selection.start === selection.end;
}
