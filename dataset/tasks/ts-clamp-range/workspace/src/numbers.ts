/** Sum of a list of numbers; 0 for an empty list. */
export function sum(values: readonly number[]): number {
  let total = 0;
  for (const v of values) total += v;
  return total;
}

/** Arithmetic mean. Throws RangeError for an empty list. */
export function mean(values: readonly number[]): number {
  if (values.length === 0) throw new RangeError("mean of an empty list");
  return sum(values) / values.length;
}
