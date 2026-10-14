import { test } from "node:test";
import assert from "node:assert/strict";
import { TodoService } from "../src/todos.ts";
import { handleTodos } from "../src/http.ts";

// createdAt values are deliberately not in id order.
function board() {
  const times = [500, 100, 300, 300, 200, 400];
  let i = 0;
  const service = new TodoService(() => times[i++]);
  service.add({ title: "Buy milk", tags: ["home", "Errand"], due: "2026-05-02" }); // 1
  service.add({ title: "file taxes", tags: ["finance", "urgent"], due: "2026-04-15" }); // 2
  service.add({ title: "call plumber", tags: ["home", "urgent"] }); // 3
  service.add({ title: "Book flights", tags: ["travel"], due: "2026-05-02" }); // 4
  service.add({ title: "buy MILK frother", tags: ["HOME"], due: "2026-06-01" }); // 5
  service.add({ title: "renew passport", tags: ["travel", "urgent"] }); // 6
  service.complete(2);
  service.complete(4);
  return service;
}

const ids = (todos: { id: number }[]) => todos.map((t) => t.id);

test("no query returns everything in id order", () => {
  assert.deepEqual(ids(board().query()), [1, 2, 3, 4, 5, 6]);
  assert.deepEqual(ids(board().query({})), [1, 2, 3, 4, 5, 6]);
});

test("status filter", () => {
  const service = board();
  assert.deepEqual(ids(service.query({ status: "open" })), [1, 3, 5, 6]);
  assert.deepEqual(ids(service.query({ status: "done" })), [2, 4]);
  assert.deepEqual(ids(service.query({ status: "all" })), [1, 2, 3, 4, 5, 6]);
});

test("tags must all match, case-insensitively", () => {
  const service = board();
  assert.deepEqual(ids(service.query({ tags: ["home"] })), [1, 3, 5]);
  assert.deepEqual(ids(service.query({ tags: ["Home", "URGENT"] })), [3]);
  assert.deepEqual(ids(service.query({ tags: ["errand"] })), [1]);
  assert.deepEqual(ids(service.query({ tags: [] })), [1, 2, 3, 4, 5, 6]);
});

test("text filter is a trimmed, case-insensitive substring", () => {
  const service = board();
  assert.deepEqual(ids(service.query({ text: "  milk " })), [1, 5]);
  assert.deepEqual(ids(service.query({ text: "   " })), [1, 2, 3, 4, 5, 6]);
});

test("dueBefore is inclusive and excludes todos without a due date", () => {
  const service = board();
  assert.deepEqual(ids(service.query({ dueBefore: "2026-05-02" })), [1, 2, 4]);
  assert.deepEqual(ids(service.query({ dueBefore: "2026-05-01" })), [2]);
});

test("filters combine", () => {
  assert.deepEqual(ids(board().query({ status: "open", tags: ["home"], dueBefore: "2026-12-31" })), [1, 5]);
});

test("sort by due: nulls last in both orders, ties by id ascending", () => {
  const service = board();
  assert.deepEqual(ids(service.query({ sort: "due" })), [2, 1, 4, 5, 3, 6]);
  assert.deepEqual(ids(service.query({ sort: "due", order: "desc" })), [5, 1, 4, 2, 3, 6]);
});

test("sort by created with ties by id ascending", () => {
  const service = board();
  assert.deepEqual(ids(service.query({ sort: "created" })), [2, 5, 3, 4, 6, 1]);
  assert.deepEqual(ids(service.query({ sort: "created", order: "desc" })), [1, 6, 3, 4, 5, 2]);
});

test("sort by title ignores case", () => {
  const service = board();
  assert.deepEqual(ids(service.query({ sort: "title" })), [4, 1, 5, 3, 2, 6]);
  assert.deepEqual(ids(service.query({ sort: "id", order: "desc" })), [6, 5, 4, 3, 2, 1]);
});

test("invalid queries throw RangeError", () => {
  const service = board();
  assert.throws(() => service.query({ status: "closed" as never }), RangeError);
  assert.throws(() => service.query({ sort: "priority" as never }), RangeError);
  assert.throws(() => service.query({ order: "up" as never }), RangeError);
  assert.throws(() => service.query({ dueBefore: "2026-02-30" }), RangeError);
  assert.throws(() => service.query({ dueBefore: "2026-2-3" }), RangeError);
});

test("query does not reorder the service's list", () => {
  const service = board();
  service.query({ sort: "title", order: "desc" });
  assert.deepEqual(ids(service.list()), [1, 2, 3, 4, 5, 6]);
});

test("HTTP: query-string parameters", () => {
  const res = handleTodos(board(), "/todos?status=open&tag=home&tag=&q=MILK&sort=due&order=desc&page=3");
  assert.equal(res.status, 200);
  const body = res.body as { items: { id: number }[]; count: number };
  assert.deepEqual(ids(body.items), [5, 1]);
  assert.equal(body.count, 2);
});

test("HTTP: repeated tag parameters and dueBefore", () => {
  const res = handleTodos(board(), "/todos?tag=travel&tag=urgent");
  assert.deepEqual(ids((res.body as { items: { id: number }[] }).items), [6]);
  const due = handleTodos(board(), "/todos?dueBefore=2026-04-30");
  assert.deepEqual(ids((due.body as { items: { id: number }[] }).items), [2]);
});

test("HTTP: no parameters lists everything", () => {
  const res = handleTodos(board(), "/todos");
  assert.equal(res.status, 200);
  assert.equal((res.body as { count: number }).count, 6);
});

test("HTTP: invalid values give 400 with an error string", () => {
  for (const qs of ["status=closed", "sort=priority", "order=sideways", "dueBefore=tomorrow", "dueBefore=2026-13-01"]) {
    const res = handleTodos(board(), `/todos?${qs}`);
    assert.equal(res.status, 400, qs);
    assert.equal(typeof (res.body as { error: unknown }).error, "string");
  }
});
