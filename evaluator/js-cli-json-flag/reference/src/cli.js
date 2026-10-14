import { addCounts, count } from "./count.js";

const USAGE = "usage: tally [--json] [file ...]";

function row(counts, label) {
  const cell = (n) => String(n).padStart(7) + " ";
  return cell(counts.lines) + cell(counts.words) + cell(counts.chars) + label;
}

/**
 * Run the CLI.
 * @param {string[]} argv arguments after the program name
 * @param {{ readFile(path: string): string, stdout(text: string): void, stderr(text: string): void }} io
 * @returns {number} the exit code
 */
export function run(argv, io) {
  const paths = [];
  let json = false;
  for (const arg of argv) {
    if (arg === "--json") {
      json = true;
      continue;
    }
    if (arg.startsWith("-")) {
      io.stderr(`tally: unknown option ${arg}\n${USAGE}\n`);
      return 2;
    }
    paths.push(arg);
  }

  let exitCode = 0;
  let total = { lines: 0, words: 0, chars: 0 };
  const rows = [];
  const files = [];
  for (const path of paths) {
    let text;
    try {
      text = io.readFile(path);
    } catch {
      io.stderr(`tally: cannot read ${path}\n`);
      exitCode = 1;
      continue;
    }
    const counts = count(text);
    total = addCounts(total, counts);
    rows.push(row(counts, path));
    files.push({ path, ...counts });
  }
  if (json) {
    io.stdout(JSON.stringify({ files, total }) + "\n");
    return exitCode;
  }
  if (paths.length > 1) rows.push(row(total, "total"));
  if (rows.length > 0) io.stdout(rows.join("\n") + "\n");
  return exitCode;
}
