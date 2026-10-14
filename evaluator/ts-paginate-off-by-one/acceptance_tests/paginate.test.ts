import { test } from "node:test";
import assert from "node:assert/strict";
import { paginate } from "../src/paginate.ts";
import { listOrders } from "../src/orders.ts";

const range = (n: number) => Array.from({ length: n }, (_, i) => i + 1);

test("first page starts at the first item", () => {
  const page = paginate(range(25), 1, 10);
  assert.deepEqual(page.items, range(10));
  assert.equal(page.hasPrev, false);
  assert.equal(page.hasNext, true);
});

test("middle and last page", () => {
  assert.deepEqual(paginate(range(25), 2, 10).items, range(20).slice(10));
  const last = paginate(range(25), 3, 10);
  assert.deepEqual(last.items, [21, 22, 23, 24, 25]);
  assert.equal(last.totalPages, 3);
  assert.equal(last.hasNext, false);
  assert.equal(last.hasPrev, true);
});

test("exact multiple of the page size", () => {
  const last = paginate(range(20), 2, 10);
  assert.equal(last.totalPages, 2);
  assert.deepEqual(last.items, range(20).slice(10));
  assert.equal(last.hasNext, false);
});

test("past the end", () => {
  const page = paginate(range(5), 3, 2);
  assert.deepEqual(page.items, [5]);
  const beyond = paginate(range(5), 4, 2);
  assert.deepEqual(beyond.items, []);
  assert.equal(beyond.hasNext, false);
  assert.equal(beyond.totalPages, 3);
});

test("empty list", () => {
  assert.deepEqual(paginate([], 1, 10), {
    items: [],
    page: 1,
    pageSize: 10,
    totalItems: 0,
    totalPages: 0,
    hasNext: false,
    hasPrev: false,
  });
});

test("fewer items than one page", () => {
  const page = paginate(["a", "b"], 1, 10);
  assert.deepEqual(page.items, ["a", "b"]);
  assert.equal(page.totalPages, 1);
  assert.equal(page.hasNext, false);
});

test("page size one", () => {
  assert.deepEqual(paginate(["a", "b", "c"], 3, 1).items, ["c"]);
  assert.equal(paginate(["a", "b", "c"], 2, 1).hasNext, true);
});

test("input is not modified", () => {
  const items = range(7);
  paginate(items, 2, 3);
  assert.deepEqual(items, range(7));
});

test("listOrders uses page 1 and size 10 by default", () => {
  const orders = range(25).map((id) => ({ id, customer: `c${id}`, totalCents: id * 100 }));
  const page = listOrders(orders, {});
  assert.deepEqual(page.items.map((o) => o.id), range(10));
  assert.equal(page.totalPages, 3);
  assert.deepEqual(listOrders(orders, { page: "3" }).items.map((o) => o.id), [21, 22, 23, 24, 25]);
});
