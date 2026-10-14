/**
 * @typedef {{ name: string, startedAt: number, finishedAt: number }} Step
 */

/**
 * Duration of each step in milliseconds, in the original order.
 * @param {Step[]} steps
 * @returns {{ name: string, ms: number }[]}
 */
export function stepDurations(steps) {
  return steps.map((s) => ({ name: s.name, ms: s.finishedAt - s.startedAt }));
}

/**
 * The slowest step, or null for an empty list. Ties go to the earlier step.
 * @param {Step[]} steps
 */
export function slowestStep(steps) {
  let best = null;
  for (const d of stepDurations(steps)) {
    if (best === null || d.ms > best.ms) best = d;
  }
  return best;
}
