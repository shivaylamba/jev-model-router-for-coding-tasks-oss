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
