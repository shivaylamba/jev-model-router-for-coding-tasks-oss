# apiclient

The internal HTTP API client and the service wrappers built on it
(`src/users.js`, `src/billing.js`, `src/reports.js`). `client.request()` does
not perform I/O itself: it describes the request and hands it to the
`transport` function you give it, so the same code runs against `fetch`, a
queue, or a fake in tests.

Deprecations go through `src/deprecate.js`, which reports each deprecation code
once per process and lets tests capture warnings with `setDeprecationHandler`.

Node 24, no dependencies. Run the tests with `node --test`.
