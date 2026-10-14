export type OrderLine = {
  sku: string;
  /** Price of one unit in cents (integer, >= 0). */
  unitPrice: number;
  /** Number of units (integer, >= 1). */
  quantity: number;
};

export type Order = {
  lines: OrderLine[];
};

export type Coupon = {
  code: string;
  /** "percent": value is a whole-number percentage. "fixed": value is cents off. */
  kind: "percent" | "fixed";
  value: number;
  /** The coupon only applies when the merchandise total is at least this many cents. */
  minSubtotal?: number;
};

export type CouponStatus = "none" | "applied" | "below-minimum";

export type Discount = {
  /** Which rule produced it, e.g. "volume" or "coupon:SPRING10". */
  rule: string;
  /** Cents taken off (always > 0). */
  amount: number;
};

export type Totals = {
  /** Sum of unitPrice * quantity over all lines. */
  subtotal: number;
  /** Every discount applied, in the order the rules produced them. */
  discounts: Discount[];
  /** subtotal minus all discounts. */
  merchandise: number;
  shipping: number;
  tax: number;
  /** merchandise + shipping + tax. */
  total: number;
  coupon: CouponStatus;
};
