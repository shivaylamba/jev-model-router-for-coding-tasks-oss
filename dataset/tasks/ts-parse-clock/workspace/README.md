# shiftclock

Time-of-day helpers for the shift scheduler. Times are stored as minutes after
midnight (0 to 1439).

Node 24 runs the `.ts` files directly through type stripping, so use only
erasable TypeScript syntax (no `enum`, `namespace` or constructor parameter
properties) and include the `.ts` extension in relative imports.

Run the tests with `node --test`.
