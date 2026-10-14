# numkit

Small numeric helpers shared by our dashboards (sums, averages, ranges).

Written in TypeScript and run directly by Node 24 through type stripping, so there is no build step. That means only erasable syntax works (no `enum`, `namespace` or constructor parameter properties), and relative imports must include the `.ts` extension.

Run the tests with:

```
node --test
```
