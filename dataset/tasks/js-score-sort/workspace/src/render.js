import { topPlayers } from "./leaderboard.js";

/** Render the top `n` players as fixed-width lines: "  1. ALICE      1200". */
export function renderBoard(players, n = 10) {
  return topPlayers(players, n)
    .map((p) => `${String(p.rank).padStart(3)}. ${p.name.toUpperCase().padEnd(10)}${String(p.score).padStart(6)}`)
    .join("\n");
}
