import { test } from "node:test";
import assert from "node:assert/strict";
import { renderBoard } from "../src/render.js";

test("renders one line per player", () => {
  const board = renderBoard([{ name: "ada", score: 5 }]);
  assert.equal(board, "  1. ADA            5");
});
