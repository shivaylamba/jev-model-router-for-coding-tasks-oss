# catalog-gateway

The gateway in front of the product catalog API. Product lookups are slow, so
the gateway caches them.

- `src/productService.ts`: product lookups, currently with an ad-hoc `Map` cache.
- `docs/ASYNC_CACHE.md`: the design of the shared async cache that will replace it.

TypeScript, run directly by Node 24's type stripping (no build step). Only
erasable syntax works: no `enum`, `namespace` or constructor parameter
properties, and relative imports include the `.ts` extension.

No dependencies. Run the tests with:

    node --test
