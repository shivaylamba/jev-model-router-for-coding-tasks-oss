import { test } from "node:test";
import assert from "node:assert/strict";
import { rankPlayers, topPlayers } from "../src/leaderboard.js";

const names = (ranked) => ranked.map((p) => p.name);

test("numeric order, highest first", () => {
  const players = [
    { name: "kim", score: 9 },
    { name: "lee", score: 85 },
    { name: "amy", score: 120 },
    { name: "bob", score: 1000 },
  ];
  assert.deepEqual(names(rankPlayers(players)), ["bob", "amy", "lee", "kim"]);
});

test("negative and fractional scores", () => {
  const players = [
    { name: "a", score: -10 },
    { name: "b", score: -5 },
    { name: "c", score: 0 },
    { name: "d", score: 2.5 },
    { name: "e", score: 10 },
    { name: "f", score: -100 },
  ];
  assert.deepEqual(names(rankPlayers(players)), ["e", "d", "c", "b", "a", "f"]);
});

test("ties are ordered by name and share a rank", () => {
  const players = [
    { name: "zed", score: 50 },
    { name: "ann", score: 50 },
    { name: "max", score: 70 },
    { name: "bea", score: 9 },
    { name: "cal", score: 50 },
  ];
  assert.deepEqual(rankPlayers(players), [
    { rank: 1, name: "max", score: 70 },
    { rank: 2, name: "ann", score: 50 },
    { rank: 2, name: "cal", score: 50 },
    { rank: 2, name: "zed", score: 50 },
    { rank: 5, name: "bea", score: 9 },
  ]);
});

test("input is not modified", () => {
  const players = [
    { name: "x", score: 3 },
    { name: "y", score: 30 },
  ];
  const copy = structuredClone(players);
  rankPlayers(players);
  assert.deepEqual(players, copy);
});

test("topPlayers takes the real top n", () => {
  const players = [
    { name: "p1", score: 9 },
    { name: "p2", score: 10 },
    { name: "p3", score: 100 },
    { name: "p4", score: 11 },
  ];
  assert.deepEqual(names(topPlayers(players, 2)), ["p3", "p4"]);
});

test("ranks skip after a tie, as 1, 2, 2, 4", () => {
  const players = [
    { name: "d", score: 1 },
    { name: "c", score: 20 },
    { name: "b", score: 20 },
    { name: "a", score: 300 },
  ];
  assert.deepEqual(rankPlayers(players).map((p) => p.rank), [1, 2, 2, 4]);
  assert.deepEqual(names(rankPlayers(players)), ["a", "b", "c", "d"]);
});

test("empty board", () => {
  assert.deepEqual(rankPlayers([]), []);
});
