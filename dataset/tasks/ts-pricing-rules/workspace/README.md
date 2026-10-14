# checkout-pricing

Order pricing for the shop's checkout: discounts, coupons, shipping and tax.
All amounts are integer cents.

- `src/types.ts`: orders, coupons and the `Totals` result.
- `src/money.ts`: cent arithmetic (`percentOf`, `formatCents`).
- `src/pricing.ts`: `orderTotal(order, coupon?)`.
- `src/checkout.ts`: builds the receipt lines shown to the customer.
- `docs/PRICING.md`: the pricing rules.

TypeScript, run directly by Node 24's type stripping (no build step). Only
erasable syntax works: no `enum`, `namespace` or constructor parameter
properties, and relative imports include the `.ts` extension.

No dependencies. Run the tests with:

    node --test
