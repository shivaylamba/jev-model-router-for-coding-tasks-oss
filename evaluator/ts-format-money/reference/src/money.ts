export type Currency = "USD" | "EUR" | "GBP";

export interface LineItem {
  description: string;
  quantity: number;
  unitCents: number;
}

/** Total of all line items, in cents. */
export function totalCents(items: readonly LineItem[]): number {
  return items.reduce((acc, item) => acc + item.quantity * item.unitCents, 0);
}

const SYMBOLS: Record<Currency, string> = { USD: "$", EUR: "€", GBP: "£" };

/** Format integer cents as "-$1,234.56". */
export function formatCents(cents: number, currency: Currency): string {
  if (typeof cents !== "number" || !Number.isInteger(cents)) {
    throw new TypeError(`cents must be an integer, got ${String(cents)}`);
  }
  if (!Object.hasOwn(SYMBOLS, currency)) {
    throw new RangeError(`unsupported currency ${String(currency)}`);
  }
  const negative = cents < 0;
  const abs = Math.abs(cents);
  const whole = Math.floor(abs / 100);
  const frac = String(abs % 100).padStart(2, "0");
  const grouped = String(whole).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return `${negative ? "-" : ""}${SYMBOLS[currency]}${grouped}.${frac}`;
}
