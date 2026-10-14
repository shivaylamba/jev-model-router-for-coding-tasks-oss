import type { TodoQuery, TodoService } from "./todos.ts";

export interface Response {
  status: number;
  body: unknown;
}

/** Handle GET /todos. `url` is the request path plus query string, e.g. "/todos?status=open". */
export function handleTodos(service: TodoService, url: string): Response {
  const parsed = new URL(url, "http://localhost");
  if (parsed.pathname !== "/todos") {
    return { status: 404, body: { error: "not found" } };
  }
  const params = parsed.searchParams;
  const query: TodoQuery = {};
  const status = params.get("status");
  if (status !== null) query.status = status as TodoQuery["status"];
  const tags = params.getAll("tag").filter((tag) => tag !== "");
  if (tags.length > 0) query.tags = tags;
  const text = params.get("q");
  if (text !== null) query.text = text;
  const dueBefore = params.get("dueBefore");
  if (dueBefore !== null) query.dueBefore = dueBefore;
  const sort = params.get("sort");
  if (sort !== null) query.sort = sort as TodoQuery["sort"];
  const order = params.get("order");
  if (order !== null) query.order = order as TodoQuery["order"];

  let items;
  try {
    items = service.query(query);
  } catch (err) {
    if (err instanceof RangeError) return { status: 400, body: { error: err.message } };
    throw err;
  }
  return { status: 200, body: { items, count: items.length } };
}
