# Filtering and sorting todos (agreed design)

The board needs to filter and sort the list. This is what we agreed on in the
planning thread; it has not been built yet.

## `TodoService.query(query?: TodoQuery): Todo[]`

```ts
export interface TodoQuery {
  status?: "open" | "done" | "all";      // default "all"
  tags?: string[];                       // default: no tag filter
  text?: string;                         // default: no text filter
  dueBefore?: string;                    // "YYYY-MM-DD"
  sort?: "id" | "created" | "due" | "title"; // default "id"
  order?: "asc" | "desc";                // default "asc"
}
```

Filters (all given filters must match):

- `status`: `"open"` or `"done"` keeps only todos with that status; `"all"` keeps everything.
- `tags`: the todo must carry **every** listed tag. Tags compare case-insensitively.
  An empty array means no tag filter.
- `text`: case-insensitive substring match on the title. The text is trimmed first;
  if nothing is left, there is no text filter.
- `dueBefore`: keeps todos due **on or before** that date. Todos without a due
  date never match this filter.

Sorting:

- `id`: by id. `created`: by `createdAt`. `due`: by due date. `title`: by the
  lowercased title, compared by plain string comparison (`<`), not locale rules.
- `order: "desc"` reverses the sort key.
- Todos without a due date always come **last** when sorting by `due`, in both orders.
- Ties (equal sort keys, including several todos without a due date) are always
  broken by id **ascending**, whatever the order.

Validation: `query` throws a `RangeError` for a `status`, `sort` or `order` value
not listed above, and for a `dueBefore` that is not a real calendar date written
as `YYYY-MM-DD` (so `"2026-02-30"` and `"2026-2-3"` are rejected).

`query` returns a new array; the service's own list is never reordered.

## HTTP: `GET /todos?...`

`handleTodos(service, url)` reads these query-string parameters:

| parameter   | maps to            |
|-------------|--------------------|
| `status`    | `status`           |
| `tag`       | `tags`; repeat the parameter for several tags (`tag=home&tag=urgent`); empty values are ignored |
| `q`         | `text`             |
| `dueBefore` | `dueBefore`        |
| `sort`      | `sort`             |
| `order`     | `order`            |

Other parameters are ignored. A parameter that is absent means "use the default".
On success the response is `{ status: 200, body: { items, count } }` where
`count` is `items.length`. Invalid values give `{ status: 400, body: { error } }`
with `error` a human-readable string.
