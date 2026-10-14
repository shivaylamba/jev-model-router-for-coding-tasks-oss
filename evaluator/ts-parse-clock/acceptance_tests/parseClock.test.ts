import { test } from "node:test";
import assert from "node:assert/strict";
import { parseClock } from "../src/clock.ts";

test("24-hour form", () => {
  assert.equal(parseClock("19:30"), 1170);
  assert.equal(parseClock("00:00"), 0);
  assert.equal(parseClock("7:05"), 425);
  assert.equal(parseClock("23:59"), 1439);
});

test("12-hour form with and without minutes", () => {
  assert.equal(parseClock("7:30 pm"), 1170);
  assert.equal(parseClock("7pm"), 1140);
  assert.equal(parseClock("7:30am"), 450);
  assert.equal(parseClock("11:59 PM"), 1439);
  assert.equal(parseClock("9 Am"), 540);
});

test("12am and 12pm", () => {
  assert.equal(parseClock("12am"), 0);
  assert.equal(parseClock("12:15 am"), 15);
  assert.equal(parseClock("12pm"), 720);
  assert.equal(parseClock("12:45 pm"), 765);
});

test("surrounding whitespace is ignored", () => {
  assert.equal(parseClock("  08:15 "), 495);
});

test("out-of-range values throw RangeError", () => {
  assert.throws(() => parseClock("24:00"), RangeError);
  assert.throws(() => parseClock("7:60"), RangeError);
  assert.throws(() => parseClock("13pm"), RangeError);
  assert.throws(() => parseClock("0am"), RangeError);
  assert.throws(() => parseClock("00:30 am"), RangeError);
});

test("malformed input throws SyntaxError", () => {
  assert.throws(() => parseClock(""), SyntaxError);
  assert.throws(() => parseClock("7"), SyntaxError);
  assert.throws(() => parseClock("7:5"), SyntaxError);
  assert.throws(() => parseClock("noon"), SyntaxError);
  assert.throws(() => parseClock("7:30 p.m."), SyntaxError);
  assert.throws(() => parseClock("-1:00"), SyntaxError);
});
