# pinned

Version helpers for our internal plugin registry: parse and compare release
versions, and (soon) check versions against dependency ranges. Range syntax is
documented in `docs/RANGES.md`.

Node 24 runs the `.ts` files directly through type stripping, so use only
erasable TypeScript syntax (no `enum`, `namespace` or constructor parameter
properties) and include the `.ts` extension in relative imports.

Run the tests with `node --test`.
