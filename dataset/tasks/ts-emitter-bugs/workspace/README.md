# minibus

A tiny typed event emitter (`src/emitter.ts`) and the key-value store built on
it (`src/store.ts`) that our settings panel uses to react to changes.

TypeScript, run directly by Node 24 through type stripping: only erasable
syntax works (no `enum`, `namespace` or constructor parameter properties) and
relative imports include the `.ts` extension. No dependencies.

Run the tests with `node --test`.
