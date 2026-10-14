# invoice-kit

Helpers for building invoice line items. Amounts are always stored as integer
cents to avoid floating-point rounding.

Written in TypeScript and run directly by Node 24 through type stripping, so there
is no build step. Only erasable syntax works (no `enum`, `namespace` or constructor
parameter properties), and relative imports must include the `.ts` extension.

Run the tests with:

```
node --test
```
