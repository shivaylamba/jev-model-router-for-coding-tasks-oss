# tinyschema

A small validator for the subset of JSON Schema our config files and webhook
payloads use. It reports every problem it finds as `{ path, keyword }` pairs so
the admin UI can highlight the offending field. The supported subset and the
exact reporting rules are in [SPEC.md](SPEC.md).

TypeScript, run directly by Node 24 through type stripping: only erasable
syntax works (no `enum`, `namespace` or constructor parameter properties) and
relative imports include the `.ts` extension. No dependencies.

Run the tests with `node --test`.

- `src/types.ts`: `Schema`, `ValidationError`, `SchemaError`.
- `src/pointer.ts`: JSON Pointer helpers.
- `src/validate.ts`: `validate(schema, data)`.
