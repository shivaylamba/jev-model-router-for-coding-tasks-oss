# signup-service

Server-side checks for the account sign-up form. The web form does its own
checks, but this service is the source of truth: the rules are in
[docs/signup-rules.md](docs/signup-rules.md).

TypeScript, run directly by Node 24 through type stripping, so only erasable
syntax works (no `enum`, `namespace` or constructor parameter properties) and
relative imports include the `.ts` extension. No dependencies.

Run the tests with `node --test`.

- `src/types.ts`: input, result and error-code types.
- `src/dates.ts`: calendar helpers.
- `src/signup.ts`: `validateSignup`.
- `src/handler.ts`: turns a request body into a response.
