# devserver-config

Loads the JSON configuration file for our local dev server.

TypeScript, run directly by Node 24's type stripping (no build step). Only
erasable syntax works: no `enum`, `namespace` or constructor parameter
properties, and relative imports include the `.ts` extension.

No dependencies. Run the tests with:

    node --test
