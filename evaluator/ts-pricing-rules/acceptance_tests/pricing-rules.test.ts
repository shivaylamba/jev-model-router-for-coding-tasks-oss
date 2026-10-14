import { test } from "node:test";
import assert from "node:assert/strict";
import { orderTotal } from "../src/pricing.ts";
import { BUNDLES } from "../src/bundles.ts";
import {
  bundleRule,
  couponRule,
  createPricer,
  defaultRules,
  merchandiseTotal,
  shippingRule,
  taxRule,
  volumeRule,
  type PricingContext,
  type PricingRule,
} from "../src/rules.ts";

const line = (sku: string, unitPrice: number, quantity: number) => ({ sku, unitPrice, quantity });
const deskSetup = () => [line("DESK", 20000, 1), line("CHAIR", 12000, 1), line("LAMP", 3000, 1)];

function snapshotRule(name: string, seen: PricingContext[]): PricingRule {
  return {
    name,
    apply(ctx) {
      seen.push({
        order: ctx.order,
        coupon: ctx.coupon,
        lines: ctx.lines.map((l) => ({ sku: l.sku, unitPrice: l.unitPrice, quantity: l.quantity, gross: l.gross, bundled: l.bundled })),
        subtotal: ctx.subtotal,
        discounts: ctx.discounts.map((d) => ({ ...d })),
        couponStatus: ctx.couponStatus,
        shipping: ctx.shipping,
        tax: ctx.tax,
      });
    },
  };
}

test("default rules are the five named rules in order", () => {
  assert.deepEqual(defaultRules.map((rule) => rule.name), ["bundle", "volume", "coupon", "shipping", "tax"]);
  assert.equal(bundleRule([]).name, "bundle");
  assert.deepEqual(BUNDLES, [
    { id: "desk-setup", skus: ["DESK", "CHAIR", "LAMP"], percent: 15 },
    { id: "lighting", skus: ["LAMP", "BULB"], percent: 10 },
  ]);
});

test("existing behaviour without bundles is unchanged", () => {
  assert.deepEqual(
    orderTotal({ lines: [line("PAPER", 1999, 3)] }, { code: "BIGFIX", kind: "fixed", value: 10000 }),
    { subtotal: 5997, discounts: [{ rule: "coupon:BIGFIX", amount: 5997 }], merchandise: 0, shipping: 499, tax: 0, total: 499, coupon: "applied" },
  );
  const atThreshold = orderTotal({ lines: [line("PAPER", 2500, 2)] });
  assert.deepEqual([atThreshold.shipping, atThreshold.tax, atThreshold.total], [0, 400, 5400]);
  assert.deepEqual(orderTotal({ lines: [] }, { code: "P", kind: "percent", value: 20 }), {
    subtotal: 0, discounts: [], merchandise: 0, shipping: 0, tax: 0, total: 0, coupon: "applied",
  });
  assert.throws(() => orderTotal({ lines: [line("PEN", -1, 1)] }), RangeError);
  assert.throws(() => orderTotal({ lines: [line("PEN", 100, 2.5)] }), RangeError);
});

test("createPricer with no rules only sums the lines", () => {
  const price = createPricer([]);
  assert.deepEqual(price({ lines: [line("PEN", 250, 4)] }, { code: "X", kind: "fixed", value: 100 }), {
    subtotal: 1000, discounts: [], merchandise: 1000, shipping: 0, tax: 0, total: 1000, coupon: "none",
  });
});

test("createPricer validates before running any rule", () => {
  let ran = false;
  const price = createPricer([{ name: "spy", apply() { ran = true; } }]);
  assert.throws(() => price({ lines: [line("PEN", 250, 0)] }), RangeError);
  assert.equal(ran, false);
});

test("rules run once each, in order, with a fresh context per call", () => {
  const log: string[] = [];
  const logRule = (name: string): PricingRule => ({
    name,
    apply(ctx) {
      log.push(name);
      ctx.discounts.push({ rule: name, amount: 10 });
    },
  });
  const price = createPricer([logRule("a"), logRule("b"), logRule("c")]);
  const first = price({ lines: [line("PEN", 250, 4)] });
  const second = price({ lines: [line("PEN", 250, 4)] });
  assert.deepEqual(log, ["a", "b", "c", "a", "b", "c"]);
  assert.deepEqual(first.discounts.map((d) => d.rule), ["a", "b", "c"]);
  assert.deepEqual(second, first);
  assert.equal(first.merchandise, 970);
});

test("the context handed to rules", () => {
  const seen: PricingContext[] = [];
  const coupon = { code: "C", kind: "fixed" as const, value: 5 };
  createPricer([snapshotRule("spy", seen)])({ lines: [line("PEN", 250, 4), line("INK", 900, 1)] }, coupon);
  const ctx = seen[0];
  assert.deepEqual(ctx.lines, [
    { sku: "PEN", unitPrice: 250, quantity: 4, gross: 1000, bundled: 0 },
    { sku: "INK", unitPrice: 900, quantity: 1, gross: 900, bundled: 0 },
  ]);
  assert.deepEqual(
    [ctx.subtotal, ctx.discounts, ctx.couponStatus, ctx.shipping, ctx.tax, ctx.coupon],
    [1900, [], "none", 0, 0, coupon],
  );
});

test("a rule inserted before shipping and tax affects them", () => {
  const staff: PricingRule = { name: "staff", apply(ctx) { ctx.discounts.push({ rule: "staff", amount: 1000 }); } };
  const order = { lines: [line("PAPER", 2500, 2)] };
  const before = createPricer([volumeRule, couponRule, staff, shippingRule, taxRule])(order);
  assert.deepEqual([before.merchandise, before.shipping, before.tax, before.total], [4000, 499, 320, 4819]);
  const after = createPricer([volumeRule, couponRule, shippingRule, taxRule, staff])(order);
  assert.deepEqual([after.merchandise, after.shipping, after.tax, after.total], [4000, 0, 400, 4400]);
});

test("default bundle via orderTotal", () => {
  assert.deepEqual(orderTotal({ lines: deskSetup() }), {
    subtotal: 35000,
    discounts: [{ rule: "bundle:desk-setup", amount: 5250 }],
    merchandise: 29750,
    shipping: 0,
    tax: 2380,
    total: 32130,
    coupon: "none",
  });
});

test("bundle discount is rounded per line", () => {
  const price = createPricer([bundleRule([{ id: "pair", skus: ["A", "B"], percent: 15 }])]);
  assert.deepEqual(price({ lines: [line("A", 110, 1), line("B", 110, 1)] }).discounts, [{ rule: "bundle:pair", amount: 34 }]);
  assert.deepEqual(price({ lines: [line("A", 110, 3), line("B", 110, 3)] }).discounts, [{ rule: "bundle:pair", amount: 100 }]);
  assert.deepEqual(price({ lines: [line("A", 110, 3)] }).discounts, []);
});

test("a unit belongs to one bundle; bundles form in list order", () => {
  const twoLamps = orderTotal({ lines: [...deskSetup().slice(0, 2), line("LAMP", 3000, 2), line("BULB", 500, 1)] });
  assert.deepEqual(twoLamps.discounts, [
    { rule: "bundle:desk-setup", amount: 5250 },
    { rule: "bundle:lighting", amount: 350 },
  ]);
  const oneLamp = orderTotal({ lines: [...deskSetup(), line("BULB", 500, 1)] });
  assert.deepEqual(oneLamp.discounts, [{ rule: "bundle:desk-setup", amount: 5250 }]);
  const reversed = createPricer([bundleRule([...BUNDLES].reverse())])({ lines: [...deskSetup(), line("BULB", 500, 1)] });
  assert.deepEqual(reversed.discounts, [{ rule: "bundle:lighting", amount: 350 }]);
});

test("a bundle can form several times and marks the bundled units", () => {
  const seen: PricingContext[] = [];
  const price = createPricer([bundleRule(BUNDLES), snapshotRule("spy", seen)]);
  const totals = price({ lines: [line("DESK", 20000, 2), line("CHAIR", 12000, 2), line("LAMP", 3000, 3)] });
  assert.deepEqual(totals.discounts, [{ rule: "bundle:desk-setup", amount: 10500 }]);
  assert.deepEqual(seen[0].lines.map((l) => l.bundled), [2, 2, 2]);
});

test("volume discount skips bundled units but eligibility uses the full quantity", () => {
  const twelve = orderTotal({ lines: [...deskSetup().slice(0, 2), line("LAMP", 3000, 12)] });
  assert.deepEqual(twelve.discounts, [
    { rule: "bundle:desk-setup", amount: 5250 },
    { rule: "volume", amount: 3300 },
  ]);
  const ten = orderTotal({ lines: [...deskSetup().slice(0, 2), line("LAMP", 3000, 10)] });
  assert.deepEqual(ten.discounts[1], { rule: "volume", amount: 2700 });
});

test("exclusive coupons are not combined with bundles", () => {
  const vip = { code: "VIP", kind: "percent" as const, value: 10, exclusive: true };
  const excluded = orderTotal({ lines: deskSetup() }, vip);
  assert.equal(excluded.coupon, "excluded");
  assert.deepEqual(excluded.discounts, [{ rule: "bundle:desk-setup", amount: 5250 }]);
  assert.equal(orderTotal({ lines: deskSetup() }, { ...vip, minSubtotal: 1_000_000 }).coupon, "excluded");
  const noBundle = orderTotal({ lines: [line("DESK", 20000, 1)] }, vip);
  assert.equal(noBundle.coupon, "applied");
  assert.deepEqual(noBundle.discounts, [{ rule: "coupon:VIP", amount: 2000 }]);
});

test("non-exclusive coupons use the merchandise total after bundles", () => {
  const save = orderTotal({ lines: deskSetup() }, { code: "SAVE10", kind: "percent", value: 10 });
  assert.equal(save.coupon, "applied");
  assert.deepEqual(save.discounts, [
    { rule: "bundle:desk-setup", amount: 5250 },
    { rule: "coupon:SAVE10", amount: 2975 },
  ]);
  const min = orderTotal({ lines: deskSetup() }, { code: "BIG", kind: "fixed", value: 500, minSubtotal: 30000 });
  assert.equal(min.coupon, "below-minimum");
});

test("duplicate SKU lines: bundled units come from the earliest line", () => {
  const seen: PricingContext[] = [];
  const price = createPricer([bundleRule(BUNDLES), snapshotRule("spy", seen)]);
  const totals = price({ lines: [line("LAMP", 3000, 1), line("LAMP", 2000, 1), line("BULB", 500, 1)] });
  assert.deepEqual(totals.discounts, [{ rule: "bundle:lighting", amount: 350 }]);
  assert.deepEqual(seen[0].lines.map((l) => l.bundled), [1, 0, 1]);
});

test("a bundle discount can drop the order below free shipping", () => {
  const totals = orderTotal({ lines: [line("LAMP", 3000, 1), line("BULB", 2500, 1)] });
  assert.deepEqual([totals.merchandise, totals.shipping, totals.tax, totals.total], [4950, 499, 396, 5845]);
});
