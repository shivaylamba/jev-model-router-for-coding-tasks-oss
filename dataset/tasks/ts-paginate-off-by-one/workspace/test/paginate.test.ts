import { test } from "node:test";
import assert from "node:assert/strict";
import { paginate } from "../src/paginate.ts";

test("rejects invalid arguments", () => {
  assert.throws(() => paginate([1, 2, 3], 0, 10), RangeError);
  assert.throws(() => paginate([1, 2, 3], 1, 0), RangeError);
  assert.throws(() => paginate([1, 2, 3], 1.5, 10), RangeError);
});
