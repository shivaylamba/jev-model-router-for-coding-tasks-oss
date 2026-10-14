export const MINUTES_PER_DAY = 24 * 60;

/** Format minutes after midnight as zero-padded 24-hour "HH:MM". */
export function formatClock(minutes: number): string {
  if (!Number.isInteger(minutes) || minutes < 0 || minutes >= MINUTES_PER_DAY) {
    throw new RangeError(`minutes out of range: ${minutes}`);
  }
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${String(hours).padStart(2, "0")}:${String(mins).padStart(2, "0")}`;
}

const CLOCK_PATTERN = /^(\d{1,2})(?::(\d{2}))?(?:\s*(am|pm))?$/i;

/** Parse "19:30", "7:30 pm", "7pm" or "12am" into minutes after midnight. */
export function parseClock(input: string): number {
  const match = CLOCK_PATTERN.exec(input.trim());
  if (!match) {
    throw new SyntaxError(`not a time: ${JSON.stringify(input)}`);
  }
  const [, hourText, minuteText, meridiem] = match;
  if (minuteText === undefined && meridiem === undefined) {
    throw new SyntaxError(`not a time: ${JSON.stringify(input)}`);
  }
  const hour = Number(hourText);
  const minute = minuteText === undefined ? 0 : Number(minuteText);
  if (minute > 59) {
    throw new RangeError(`minutes out of range: ${JSON.stringify(input)}`);
  }
  if (meridiem === undefined) {
    if (hour > 23) {
      throw new RangeError(`hour out of range: ${JSON.stringify(input)}`);
    }
    return hour * 60 + minute;
  }
  if (hour < 1 || hour > 12) {
    throw new RangeError(`hour out of range: ${JSON.stringify(input)}`);
  }
  const base = hour % 12;
  return (meridiem.toLowerCase() === "pm" ? base + 12 : base) * 60 + minute;
}
