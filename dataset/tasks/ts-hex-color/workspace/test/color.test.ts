import { test } from "node:test";
import assert from "node:assert/strict";
import { rgbToHex } from "../src/color.ts";

test("rgbToHex", () => {
  assert.equal(rgbToHex(255, 136, 0), "#ff8800");
  assert.throws(() => rgbToHex(256, 0, 0), RangeError);
});
