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

/** `value` limited to the closed interval [min, max]. RangeError when min > max. */
export function clamp(value: number, min: number, max: number): number {
  if (min > max) throw new RangeError(`clamp: min ${min} is greater than max ${max}`);
  if (value < min) return min;
  if (value > max) return max;
  return value;
}

/**
 * Python-style range: range(stop), range(start, stop) or range(start, stop, step).
 * RangeError when step is 0.
 */
export function range(start: number, stop?: number, step: number = 1): number[] {
  if (stop === undefined) {
    stop = start;
    start = 0;
  }
  if (step === 0) throw new RangeError("range: step must not be 0");
  const out: number[] = [];
  if (step > 0) {
    for (let v = start; v < stop; v += step) out.push(v);
  } else {
    for (let v = start; v > stop; v += step) out.push(v);
  }
  return out;
}
