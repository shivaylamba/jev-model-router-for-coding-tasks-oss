# notifier

Sends notifications through a pluggable transport (email, SMS, chat). Used by
the alerting job (`src/alerts.ts`) and the daily digest (`src/digest.ts`).

TypeScript runs directly through Node 24's type stripping: use only erasable
syntax (no `enum`, `namespace` or constructor parameter properties) and include
the `.ts` extension in relative imports.

Run the tests with `node --test`.
