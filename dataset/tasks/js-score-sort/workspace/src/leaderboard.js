/**
 * @typedef {{ name: string, score: number }} Player
 * @typedef {{ rank: number, name: string, score: number }} RankedPlayer
 */

/**
 * Rank players for the leaderboard.
 *
 * Players are ordered by score, highest first (scores are numbers and may be
 * negative or fractional). Players with the same score are ordered by name,
 * alphabetically (A before B). Ranks are 1-based; players with equal scores
 * share a rank and the next rank skips accordingly (1, 2, 2, 4).
 *
 * Returns a new array; the input array and its objects are not modified.
 *
 * @param {Player[]} players
 * @returns {RankedPlayer[]}
 */
export function rankPlayers(players) {
  const sorted = [...players].sort(
    (a, b) => String(b.score).localeCompare(String(a.score)) || a.name.localeCompare(b.name),
  );
  const ranked = [];
  sorted.forEach((player, index) => {
    const previous = ranked[index - 1];
    const rank = previous && previous.score === player.score ? previous.rank : index + 1;
    ranked.push({ rank, name: player.name, score: player.score });
  });
  return ranked;
}

/**
 * The first `n` entries of the ranked board.
 * @param {Player[]} players
 * @param {number} n
 */
export function topPlayers(players, n) {
  return rankPlayers(players).slice(0, n);
}
