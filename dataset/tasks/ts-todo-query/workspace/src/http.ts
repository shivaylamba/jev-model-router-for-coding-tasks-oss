import type { TodoService } from "./todos.ts";

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
  const items = service.list();
  return { status: 200, body: { items, count: items.length } };
}
