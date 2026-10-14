# pkgls

A command-line lister for packages in our internal registry. It prints package
names, sizes and descriptions as a plain-text table that has to fit the
terminal.

- `src/format.ts` - number and size formatting
- `src/table.ts` - plain-text table rendering (rules in `SPEC.md`)
- `src/report.ts` - builds the package listing from registry entries

Written in TypeScript and run directly by Node 24 through type stripping, so
there is no build step. Only erasable syntax works (no `enum`, `namespace` or
constructor parameter properties), and relative imports must include the `.ts`
extension. No dependencies.

Run the tests with:

```
node --test
```
