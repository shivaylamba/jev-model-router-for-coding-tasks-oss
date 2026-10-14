import { test } from "node:test";
import assert from "node:assert/strict";
import { totalCents } from "../src/money.ts";

test("totalCents", () => {
  assert.equal(totalCents([]), 0);
  assert.equal(
    totalCents([
      { description: "widget", quantity: 3, unitCents: 250 },
      { description: "gadget", quantity: 1, unitCents: 1999 },
    ]),
    2749,
  );
});
