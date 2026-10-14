/**
 * `percent` per cent of `cents`, rounded half up to a whole cent.
 * Both arguments are integers; integer arithmetic avoids floating-point drift.
 */
export function percentOf(cents: number, percent: number): number {
  return Math.floor((cents * percent + 50) / 100);
}

/** 123456 -> "$1,234.56"; negative amounts get a leading minus. */
export function formatCents(cents: number): string {
  const sign = cents < 0 ? "-" : "";
  const abs = Math.abs(cents);
  const dollars = Math.floor(abs / 100).toLocaleString("en-US");
  return `${sign}$${dollars}.${String(abs % 100).padStart(2, "0")}`;
}
