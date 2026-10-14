export type Version = { major: number; minor: number; patch: number };

const VERSION_PATTERN = /^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/;

/**
 * Parse a release version "MAJOR.MINOR.PATCH" (an optional leading "v" is
 * allowed). Throws a TypeError for anything else, including prerelease or
 * build suffixes and numbers with leading zeros.
 */
export function parseVersion(text: string): Version {
  const match = VERSION_PATTERN.exec(text.trim());
  if (!match) {
    throw new TypeError(`invalid version: ${JSON.stringify(text)}`);
  }
  return { major: Number(match[1]), minor: Number(match[2]), patch: Number(match[3]) };
}

/** Compare two versions: negative if a < b, zero if equal, positive if a > b. */
export function compareVersions(a: Version | string, b: Version | string): number {
  const left = typeof a === "string" ? parseVersion(a) : a;
  const right = typeof b === "string" ? parseVersion(b) : b;
  return left.major - right.major || left.minor - right.minor || left.patch - right.patch;
}

type Partial3 = { parts: number[] }; // 0 to 3 concrete parts; the rest are wildcards
type Bound = { version: Version; inclusive: boolean };
type Interval = { low: Bound | null; high: Bound | null; empty?: boolean };

const PART = /^(0|[1-9]\d*|x|X|\*)$/;

function parsePartial(text: string): Partial3 {
  const body = text.startsWith("v") ? text.slice(1) : text;
  const pieces = body.split(".");
  if (body === "" || pieces.length > 3) throw new TypeError(`invalid version in range: ${JSON.stringify(text)}`);
  const parts: number[] = [];
  let wild = false;
  for (const piece of pieces) {
    if (!PART.test(piece)) throw new TypeError(`invalid version in range: ${JSON.stringify(text)}`);
    const isWild = piece === "x" || piece === "X" || piece === "*";
    if (isWild) {
      wild = true;
    } else if (wild) {
      throw new TypeError(`invalid version in range: ${JSON.stringify(text)}`);
    } else {
      parts.push(Number(piece));
    }
  }
  return { parts };
}

function v(major: number, minor = 0, patch = 0): Version {
  return { major, minor, patch };
}

/** Lowest version covered by a partial. */
function floor(p: Partial3): Version {
  return v(p.parts[0] ?? 0, p.parts[1] ?? 0, p.parts[2] ?? 0);
}

/** First version above everything the partial covers (exclusive upper bound); null if unbounded. */
function ceiling(p: Partial3): Version | null {
  const [a, b, c] = p.parts;
  if (p.parts.length === 0) return null;
  if (p.parts.length === 1) return v(a + 1);
  if (p.parts.length === 2) return v(a, b + 1);
  return v(a, b, c + 1);
}

function ge(x: Version): Bound { return { version: x, inclusive: true }; }
function lt(x: Version): Bound { return { version: x, inclusive: false }; }

function comparatorInterval(op: string, p: Partial3): Interval {
  const n = p.parts.length;
  const full = n === 3;
  switch (op) {
    case "":
    case "=":
      return { low: n === 0 ? null : ge(floor(p)), high: ceiling(p) ? lt(ceiling(p)!) : null };
    case ">":
      if (n === 0) return { low: null, high: null, empty: true };
      return full ? { low: { version: floor(p), inclusive: false }, high: null } : { low: ge(ceiling(p)!), high: null };
    case ">=":
      return { low: n === 0 ? null : ge(floor(p)), high: null };
    case "<":
      if (n === 0) return { low: null, high: null, empty: true };
      return { low: null, high: lt(floor(p)) };
    case "<=":
      if (n === 0) return { low: null, high: null };
      return full ? { low: null, high: ge(floor(p)) } : { low: null, high: lt(ceiling(p)!) };
    case "~":
      if (n === 0) return { low: null, high: null };
      return { low: ge(floor(p)), high: lt(n === 1 ? v(p.parts[0] + 1) : v(p.parts[0], p.parts[1] + 1)) };
    case "^": {
      if (n === 0) return { low: null, high: null };
      const [a, b, c] = p.parts;
      let high: Version;
      if (a !== 0 || n === 1) high = v(a + 1);
      else if (b !== 0 || n === 2) high = v(0, b + 1);
      else high = v(0, 0, c + 1);
      return { low: ge(floor(p)), high: lt(high) };
    }
    default:
      throw new TypeError(`invalid operator: ${op}`);
  }
}

function inInterval(version: Version, interval: Interval): boolean {
  if (interval.empty) return false;
  if (interval.low) {
    const cmp = compareVersions(version, interval.low.version);
    if (cmp < 0 || (cmp === 0 && !interval.low.inclusive)) return false;
  }
  if (interval.high) {
    const cmp = compareVersions(version, interval.high.version);
    if (cmp > 0 || (cmp === 0 && !interval.high.inclusive)) return false;
  }
  return true;
}

const COMPARATOR = /^(<=|>=|<|>|=|~|\^)?\s*([^\s<>=~^]+)$/;

function parseAlternative(text: string): Interval[] {
  const tokens = text.split(/\s+/).filter((t) => t !== "");
  if (tokens.includes("-")) {
    if (tokens.length !== 3 || tokens[1] !== "-") throw new TypeError(`invalid hyphen range: ${JSON.stringify(text)}`);
    const lower = parsePartial(tokens[0]);
    const upper = parsePartial(tokens[2]);
    const high = upper.parts.length === 3 ? ge(floor(upper)) : ceiling(upper) ? lt(ceiling(upper)!) : null;
    return [{ low: lower.parts.length === 0 ? null : ge(floor(lower)), high }];
  }
  // Re-join operators separated from their version by whitespace.
  const comparators: string[] = [];
  for (let i = 0; i < tokens.length; i += 1) {
    if (/^(<=|>=|<|>|=|~|\^)$/.test(tokens[i])) {
      if (i + 1 >= tokens.length) throw new TypeError(`dangling operator in ${JSON.stringify(text)}`);
      comparators.push(tokens[i] + tokens[i + 1]);
      i += 1;
    } else {
      comparators.push(tokens[i]);
    }
  }
  return comparators.map((comp) => {
    const match = COMPARATOR.exec(comp);
    if (!match) throw new TypeError(`invalid comparator: ${JSON.stringify(comp)}`);
    return comparatorInterval(match[1] ?? "", parsePartial(match[2]));
  });
}

/**
 * Whether `version` satisfies `range` (see docs/RANGES.md). Throws a TypeError
 * for an invalid version or range.
 */
export function satisfies(version: string, range: string): boolean {
  const parsed = parseVersion(version);
  const alternatives = range.split("||").map(parseAlternative);
  return alternatives.some((intervals) => intervals.every((interval) => inInterval(parsed, interval)));
}
