# Pricing rules

All amounts are integer cents. Every percentage is a whole number and is
applied with `percentOf(cents, percent)` from `src/money.ts`, which rounds half
up to a whole cent.

## Validation

Before anything is priced, every line must have an integer `quantity >= 1` and
an integer `unitPrice >= 0`; otherwise pricing throws a `RangeError`.

## Current rules (in this order)

1. **Volume.** A line with `quantity >= 10` gets 10% off. The discount is
   computed and rounded per line (`percentOf(unitPrice * quantity, 10)`), then
   the per-line amounts are summed into one discount with rule `"volume"`.
2. **Coupon.** At most one coupon per order. If the merchandise total at this
   point (subtotal minus the discounts so far) is below `coupon.minSubtotal`
   (default 0), the coupon status is `"below-minimum"` and nothing is taken off.
   Otherwise the status is `"applied"` and the coupon takes off
   `percentOf(merchandise, value)` for a `"percent"` coupon, or
   `min(value, merchandise)` for a `"fixed"` coupon, recorded with rule
   `"coupon:<code>"`. With no coupon the status is `"none"`.
3. **Shipping.** 499, or free (0) when the merchandise total after all
   discounts is at least 5000. An order with no lines has no shipping.
4. **Tax.** 8% of the merchandise total after all discounts. Shipping is not
   taxed.

A discount whose amount is 0 is never recorded in `discounts`.

`total = merchandise + shipping + tax`, where
`merchandise = subtotal - sum of all discount amounts`.

## Rule pipeline (`src/rules.ts`)

Pricing is a list of rules run in order over a shared context.

```ts
export type PricedLine = {
  sku: string;
  unitPrice: number;
  quantity: number;
  gross: number;   // unitPrice * quantity
  bundled: number; // units of this line used in bundles; starts at 0
};

export type PricingContext = {
  order: Order;
  coupon: Coupon | undefined;
  lines: PricedLine[];        // one per order line, in order
  subtotal: number;           // sum of gross
  discounts: Discount[];      // starts empty; rules push onto it
  couponStatus: CouponStatus; // starts "none"; only the coupon rule changes it
  shipping: number;           // starts 0
  tax: number;                // starts 0
};

export type PricingRule = {
  name: string;
  apply(ctx: PricingContext): void;
};
```

`src/rules.ts` exports:

- the three types above;
- `merchandiseTotal(ctx)`: `ctx.subtotal` minus the sum of `ctx.discounts`
  amounts, as they stand when it is called;
- `createPricer(rules)`: returns `(order, coupon?) => Totals`. It validates the
  order (the `RangeError` rules above) before running any rule, builds a fresh
  context, calls each rule's `apply` exactly once in array order, and returns
  `{ subtotal, discounts, merchandise: merchandiseTotal(ctx), shipping, tax,
  total: merchandise + shipping + tax, coupon: ctx.couponStatus }`;
- the rules `bundleRule(bundles)` (a function returning a rule), `volumeRule`,
  `couponRule`, `shippingRule` and `taxRule`, named `"bundle"`, `"volume"`,
  `"coupon"`, `"shipping"` and `"tax"`. Rules read the merchandise total
  through `merchandiseTotal(ctx)` at the moment they run, so a rule inserted
  earlier in the list affects every later rule;
- `defaultRules`: `[bundleRule(BUNDLES), volumeRule, couponRule, shippingRule,
  taxRule]`.

`orderTotal(order, coupon?)` in `src/pricing.ts` stays as the public entry point
and prices with `defaultRules`.

## Bundle discount (new)

```ts
export type Bundle = { id: string; skus: string[]; percent: number };
```

`Bundle` lives in `src/types.ts`. `src/bundles.ts` exports `BUNDLES`, the
store's bundles:

```ts
[
  { id: "desk-setup", skus: ["DESK", "CHAIR", "LAMP"], percent: 15 },
  { id: "lighting", skus: ["LAMP", "BULB"], percent: 10 },
]
```

Rules for `bundleRule(bundles)`:

1. One bundle is one unit of every SKU in `skus` (the SKUs in a bundle are
   distinct). An order can contain the same bundle several times.
2. A unit counts towards at most one bundle. Bundles are formed in the order
   of the `bundles` array, each as many times as the still-unbundled units
   allow, before moving to the next bundle. So with DESK x1, CHAIR x1, LAMP x2,
   BULB x1, one desk-setup and one lighting bundle form; with LAMP x1 instead,
   only the desk-setup forms.
3. If several order lines have the same SKU, bundled units are taken from the
   earliest of those lines first. Each line's `bundled` count is increased by
   the units taken from it.
4. The discount is computed and rounded **per line**: for each line, add
   `percentOf(unitPrice * unitsTakenFromThisLineForThisBundle, percent)`. The
   amounts for one bundle id are summed into a single discount with rule
   `"bundle:<id>"`, recorded when the bundle is processed (so bundle discounts
   appear in `bundles` order, before the volume discount).

Interactions with the existing rules:

- **Volume.** Eligibility still uses the line's full `quantity` (>= 10), but the
  10% applies only to the line's unbundled units:
  `percentOf(unitPrice * (quantity - bundled), 10)`.
- **Exclusive coupons.** `Coupon` gains an optional `exclusive?: boolean`. An
  exclusive coupon cannot be combined with bundles: if any `"bundle:"`
  discount has been recorded when the coupon rule runs, the coupon status is
  `"excluded"` and nothing is taken off. This check comes before the minimum
  check. `CouponStatus` gains `"excluded"`. Non-exclusive coupons combine with
  bundles as usual, and their minimum and percentage use the merchandise total
  after bundle and volume discounts.
- Shipping and tax keep working from the merchandise total after all discounts.
