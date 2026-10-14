# orders-api

Listing endpoints for the orders back office. Lists are paginated with
`paginate` from `src/paginate.ts`; `src/orders.ts` uses it for the order list.

TypeScript, run directly by Node 24 through type stripping: only erasable
syntax works (no `enum`, `namespace` or constructor parameter properties) and
relative imports include the `.ts` extension. No dependencies.

Run the tests with `node --test`.
