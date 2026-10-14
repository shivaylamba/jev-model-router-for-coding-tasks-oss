import { formatCents } from "./money.ts";
import { orderTotal } from "./pricing.ts";
import type { Coupon, Order } from "./types.ts";

/** The receipt lines shown on the order confirmation page. */
export function receipt(order: Order, coupon?: Coupon): string[] {
  const totals = orderTotal(order, coupon);
  const lines = [`Subtotal ${formatCents(totals.subtotal)}`];
  for (const discount of totals.discounts) {
    lines.push(`Discount (${discount.rule}) ${formatCents(-discount.amount)}`);
  }
  if (coupon && totals.coupon === "below-minimum") {
    lines.push(`Coupon ${coupon.code} needs ${formatCents(coupon.minSubtotal ?? 0)} of merchandise`);
  }
  lines.push(`Shipping ${totals.shipping === 0 ? "free" : formatCents(totals.shipping)}`);
  lines.push(`Tax ${formatCents(totals.tax)}`);
  lines.push(`Total ${formatCents(totals.total)}`);
  return lines;
}
