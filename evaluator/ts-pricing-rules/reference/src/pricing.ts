import { createPricer, defaultRules } from "./rules.ts";
import type { Coupon, Order, Totals } from "./types.ts";

export {
  FREE_SHIPPING_THRESHOLD,
  SHIPPING_FEE,
  TAX_PERCENT,
  VOLUME_MIN_QUANTITY,
  VOLUME_PERCENT,
} from "./rules.ts";

const price = createPricer(defaultRules);

/** Price an order. See docs/PRICING.md for the rules. */
export function orderTotal(order: Order, coupon?: Coupon): Totals {
  return price(order, coupon);
}
