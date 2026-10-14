import { test } from "node:test";
import assert from "node:assert/strict";
import { orderTotal } from "../src/pricing.ts";
import { receipt } from "../src/checkout.ts";

test("plain order pays shipping and tax", () => {
  const totals = orderTotal({ lines: [{ sku: "PEN", unitPrice: 250, quantity: 4 }] });
  assert.deepEqual(totals, {
    subtotal: 1000,
    discounts: [],
    merchandise: 1000,
    shipping: 499,
    tax: 80,
    total: 1579,
    coupon: "none",
  });
});

test("volume discount is rounded per line", () => {
  const totals = orderTotal({
    lines: [
      { sku: "PEN", unitPrice: 105, quantity: 10 },
      { sku: "CLIP", unitPrice: 15, quantity: 11 },
    ],
  });
  // 105 + 16.5 -> 105 + 17
  assert.deepEqual(totals.discounts, [{ rule: "volume", amount: 122 }]);
});

test("percent coupon after volume, free shipping at 5000", () => {
  const totals = orderTotal(
    { lines: [{ sku: "NOTEBOOK", unitPrice: 600, quantity: 10 }] },
    { code: "SPRING10", kind: "percent", value: 10 },
  );
  assert.deepEqual(totals.discounts, [
    { rule: "volume", amount: 600 },
    { rule: "coupon:SPRING10", amount: 540 },
  ]);
  assert.equal(totals.merchandise, 4860);
  assert.equal(totals.shipping, 499);
  assert.equal(totals.coupon, "applied");
});

test("coupon below its minimum", () => {
  const totals = orderTotal(
    { lines: [{ sku: "PEN", unitPrice: 250, quantity: 2 }] },
    { code: "BIG", kind: "fixed", value: 1000, minSubtotal: 2000 },
  );
  assert.equal(totals.coupon, "below-minimum");
  assert.equal(totals.total, 500 + 499 + 40);
});

test("bad quantity", () => {
  assert.throws(() => orderTotal({ lines: [{ sku: "PEN", unitPrice: 250, quantity: 0 }] }), RangeError);
});

test("receipt", () => {
  assert.deepEqual(receipt({ lines: [{ sku: "INK", unitPrice: 2600, quantity: 2 }] }, { code: "FIVE", kind: "fixed", value: 500 }), [
    "Subtotal $52.00",
    "Discount (coupon:FIVE) -$5.00",
    "Shipping $4.99",
    "Tax $3.76",
    "Total $55.75",
  ]);
});
