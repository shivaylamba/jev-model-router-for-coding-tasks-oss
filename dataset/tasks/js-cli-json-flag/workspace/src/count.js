/**
 * Count lines, words and characters in a string.
 * lines: number of "\n" characters (like wc -l).
 * words: runs of non-whitespace characters.
 * chars: Unicode code points.
 */
export function count(text) {
  const lines = (text.match(/\n/g) ?? []).length;
  const words = (text.match(/\S+/g) ?? []).length;
  const chars = [...text].length;
  return { lines, words, chars };
}

export function addCounts(a, b) {
  return { lines: a.lines + b.lines, words: a.words + b.words, chars: a.chars + b.chars };
}
