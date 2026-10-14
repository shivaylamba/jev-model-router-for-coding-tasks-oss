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
