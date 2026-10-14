# appconfig

Loads layered configuration for our services: built-in defaults, then a
file, then environment overrides.

TypeScript runs directly on Node 24 through type stripping, so use only
erasable syntax (no `enum`, `namespace` or constructor parameter
properties) and include the `.ts` extension in relative imports.

Run the tests with `node --test`.
