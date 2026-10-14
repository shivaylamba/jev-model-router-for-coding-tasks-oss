export function fullName(first: string, last: string): string {
  return `${first} ${last}`.trim();
}

export function initials(name: string): string {
  return name
    .split(/[\s-]+/)
    .filter((word) => word.length > 0)
    .map((word) => word[0].toUpperCase())
    .join("");
}
