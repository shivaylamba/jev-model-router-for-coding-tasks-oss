const UNITS = [
  { key: "d", size: 86_400_000, one: "day", many: "days" },
  { key: "h", size: 3_600_000, one: "hour", many: "hours" },
  { key: "m", size: 60_000, one: "minute", many: "minutes" },
  { key: "s", size: 1_000, one: "second", many: "seconds" },
  { key: "ms", size: 1, one: "millisecond", many: "milliseconds" },
];

/**
 * Human-readable duration, e.g. "1 hour, 5 minutes" or "1h 5m".
 * @param {number} ms
 * @param {{ units?: number, style?: "long" | "compact", smallest?: "d" | "h" | "m" | "s" | "ms" }} [options]
 */
export function formatDuration(ms, options = {}) {
  if (typeof ms !== "number") throw new TypeError("ms must be a number");
  if (!Number.isFinite(ms) || ms < 0) throw new RangeError("ms must be a finite, non-negative number");
  const { units = 2, style = "long", smallest = "s" } = options;
  if (!Number.isInteger(units) || units < 1) throw new RangeError("units must be a positive integer");
  if (style !== "long" && style !== "compact") throw new RangeError(`unknown style ${style}`);
  const lastIndex = UNITS.findIndex((u) => u.key === smallest);
  if (lastIndex === -1) throw new RangeError(`unknown unit ${smallest}`);

  const label = (n, unit) => (style === "long" ? `${n} ${n === 1 ? unit.one : unit.many}` : `${n}${unit.key}`);
  let rest = Math.floor(ms);
  const parts = [];
  for (const unit of UNITS.slice(0, lastIndex + 1)) {
    const n = Math.floor(rest / unit.size);
    rest -= n * unit.size;
    if (n > 0 && parts.length < units) parts.push(label(n, unit));
  }
  if (parts.length === 0) return label(0, UNITS[lastIndex]);
  return parts.join(style === "long" ? ", " : " ");
}
