# todos

The todo service behind our team task board, plus its HTTP handler.

- `src/todos.ts`: the `Todo` type and `TodoService` (in memory; the clock is injected)
- `src/http.ts`: `handleTodos(service, url)` turns a request URL into `{ status, body }`
- `docs/`: design notes

TypeScript runs directly through Node 24's type stripping: use only erasable
syntax (no `enum`, `namespace` or constructor parameter properties) and include
the `.ts` extension in relative imports. No dependencies.

Run the tests with `node --test`.
