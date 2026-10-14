import { percentOf } from "./money.ts";
import type { Coupon, CouponStatus, Discount, Order, Totals } from "./types.ts";

export const VOLUME_MIN_QUANTITY = 10;
export const VOLUME_PERCENT = 10;
export const FREE_SHIPPING_THRESHOLD = 5000;
export const SHIPPING_FEE = 499;
export const TAX_PERCENT = 8;

/** Price an order. See docs/PRICING.md for the rules. */
export function orderTotal(order: Order, coupon?: Coupon): Totals {
  for (const line of order.lines) {
    if (!Number.isInteger(line.quantity) || line.quantity < 1) {
      throw new RangeError(`bad quantity for ${line.sku}: ${line.quantity}`);
    }
    if (!Number.isInteger(line.unitPrice) || line.unitPrice < 0) {
      throw new RangeError(`bad unit price for ${line.sku}: ${line.unitPrice}`);
    }
  }

  let subtotal = 0;
  let volume = 0;
  for (const line of order.lines) {
    const gross = line.unitPrice * line.quantity;
    subtotal += gross;
    if (line.quantity >= VOLUME_MIN_QUANTITY) {
      volume += percentOf(gross, VOLUME_PERCENT);
    }
  }

  const discounts: Discount[] = [];
  if (volume > 0) {
    discounts.push({ rule: "volume", amount: volume });
  }
  let merchandise = subtotal - volume;

  let couponStatus: CouponStatus = "none";
  if (coupon) {
    if (merchandise < (coupon.minSubtotal ?? 0)) {
      couponStatus = "below-minimum";
    } else {
      const off = coupon.kind === "percent"
        ? percentOf(merchandise, coupon.value)
        : Math.min(coupon.value, merchandise);
      couponStatus = "applied";
      if (off > 0) {
        discounts.push({ rule: `coupon:${coupon.code}`, amount: off });
        merchandise -= off;
      }
    }
  }

  let shipping = 0;
  if (order.lines.length > 0 && merchandise < FREE_SHIPPING_THRESHOLD) {
    shipping = SHIPPING_FEE;
  }
  const tax = percentOf(merchandise, TAX_PERCENT);

  return {
    subtotal,
    discounts,
    merchandise,
    shipping,
    tax,
    total: merchandise + shipping + tax,
    coupon: couponStatus,
  };
}
