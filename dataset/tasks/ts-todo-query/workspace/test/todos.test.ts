import { test } from "node:test";
import assert from "node:assert/strict";
import { TodoService } from "../src/todos.ts";
import { handleTodos } from "../src/http.ts";

function fixedClock(start: number) {
  let now = start;
  return () => now++;
}

test("add and complete", () => {
  const service = new TodoService(fixedClock(100));
  const a = service.add({ title: "  buy milk ", tags: ["home"] });
  service.add({ title: "file taxes", due: "2026-04-15" });
  assert.equal(a.title, "buy milk");
  assert.equal(a.createdAt, 100);
  assert.equal(service.complete(1).status, "done");
  assert.deepEqual(service.list().map((t) => t.id), [1, 2]);
});

test("GET /todos lists everything", () => {
  const service = new TodoService(fixedClock(0));
  service.add({ title: "a" });
  const res = handleTodos(service, "/todos");
  assert.equal(res.status, 200);
  assert.equal((res.body as { count: number }).count, 1);
  assert.equal(handleTodos(service, "/nope").status, 404);
});
