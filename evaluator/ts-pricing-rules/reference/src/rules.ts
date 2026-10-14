import { BUNDLES } from "./bundles.ts";
import { percentOf } from "./money.ts";
import type { Bundle, Coupon, CouponStatus, Discount, Order, Totals } from "./types.ts";

export const VOLUME_MIN_QUANTITY = 10;
export const VOLUME_PERCENT = 10;
export const FREE_SHIPPING_THRESHOLD = 5000;
export const SHIPPING_FEE = 499;
export const TAX_PERCENT = 8;

export type PricedLine = {
  sku: string;
  unitPrice: number;
  quantity: number;
  gross: number;
  bundled: number;
};

export type PricingContext = {
  order: Order;
  coupon: Coupon | undefined;
  lines: PricedLine[];
  subtotal: number;
  discounts: Discount[];
  couponStatus: CouponStatus;
  shipping: number;
  tax: number;
};

export type PricingRule = {
  name: string;
  apply(ctx: PricingContext): void;
};

export function merchandiseTotal(ctx: PricingContext): number {
  return ctx.discounts.reduce((left, discount) => left - discount.amount, ctx.subtotal);
}

function addDiscount(ctx: PricingContext, rule: string, amount: number): void {
  if (amount > 0) {
    ctx.discounts.push({ rule, amount });
  }
}

function validate(order: Order): void {
  for (const line of order.lines) {
    if (!Number.isInteger(line.quantity) || line.quantity < 1) {
      throw new RangeError(`bad quantity for ${line.sku}: ${line.quantity}`);
    }
    if (!Number.isInteger(line.unitPrice) || line.unitPrice < 0) {
      throw new RangeError(`bad unit price for ${line.sku}: ${line.unitPrice}`);
    }
  }
}

export function createPricer(rules: PricingRule[]): (order: Order, coupon?: Coupon) => Totals {
  const pipeline = [...rules];
  return (order, coupon) => {
    validate(order);
    const lines = order.lines.map((line) => ({
      sku: line.sku,
      unitPrice: line.unitPrice,
      quantity: line.quantity,
      gross: line.unitPrice * line.quantity,
      bundled: 0,
    }));
    const ctx: PricingContext = {
      order,
      coupon,
      lines,
      subtotal: lines.reduce((sum, line) => sum + line.gross, 0),
      discounts: [],
      couponStatus: "none",
      shipping: 0,
      tax: 0,
    };
    for (const rule of pipeline) {
      rule.apply(ctx);
    }
    const merchandise = merchandiseTotal(ctx);
    return {
      subtotal: ctx.subtotal,
      discounts: ctx.discounts.map((discount) => ({ ...discount })),
      merchandise,
      shipping: ctx.shipping,
      tax: ctx.tax,
      total: merchandise + ctx.shipping + ctx.tax,
      coupon: ctx.couponStatus,
    };
  };
}

function available(lines: PricedLine[], sku: string): number {
  return lines
    .filter((line) => line.sku === sku)
    .reduce((sum, line) => sum + line.quantity - line.bundled, 0);
}

export function bundleRule(bundles: Bundle[]): PricingRule {
  return {
    name: "bundle",
    apply(ctx) {
      for (const bundle of bundles) {
        const count = Math.min(...bundle.skus.map((sku) => available(ctx.lines, sku)));
        if (!(count > 0)) {
          continue;
        }
        let amount = 0;
        for (const sku of bundle.skus) {
          let needed = count;
          for (const line of ctx.lines) {
            if (needed === 0) break;
            if (line.sku !== sku) continue;
            const take = Math.min(needed, line.quantity - line.bundled);
            if (take === 0) continue;
            line.bundled += take;
            needed -= take;
            amount += percentOf(line.unitPrice * take, bundle.percent);
          }
        }
        addDiscount(ctx, `bundle:${bundle.id}`, amount);
      }
    },
  };
}

export const volumeRule: PricingRule = {
  name: "volume",
  apply(ctx) {
    let amount = 0;
    for (const line of ctx.lines) {
      if (line.quantity >= VOLUME_MIN_QUANTITY) {
        amount += percentOf(line.unitPrice * (line.quantity - line.bundled), VOLUME_PERCENT);
      }
    }
    addDiscount(ctx, "volume", amount);
  },
};

export const couponRule: PricingRule = {
  name: "coupon",
  apply(ctx) {
    const coupon = ctx.coupon;
    if (!coupon) {
      return;
    }
    if (coupon.exclusive && ctx.discounts.some((discount) => discount.rule.startsWith("bundle:"))) {
      ctx.couponStatus = "excluded";
      return;
    }
    const merchandise = merchandiseTotal(ctx);
    if (merchandise < (coupon.minSubtotal ?? 0)) {
      ctx.couponStatus = "below-minimum";
      return;
    }
    ctx.couponStatus = "applied";
    const off = coupon.kind === "percent" ? percentOf(merchandise, coupon.value) : Math.min(coupon.value, merchandise);
    addDiscount(ctx, `coupon:${coupon.code}`, off);
  },
};

export const shippingRule: PricingRule = {
  name: "shipping",
  apply(ctx) {
    ctx.shipping = ctx.lines.length > 0 && merchandiseTotal(ctx) < FREE_SHIPPING_THRESHOLD ? SHIPPING_FEE : 0;
  },
};

export const taxRule: PricingRule = {
  name: "tax",
  apply(ctx) {
    ctx.tax = percentOf(merchandiseTotal(ctx), TAX_PERCENT);
  },
};

export const defaultRules: PricingRule[] = [bundleRule(BUNDLES), volumeRule, couponRule, shippingRule, taxRule];
