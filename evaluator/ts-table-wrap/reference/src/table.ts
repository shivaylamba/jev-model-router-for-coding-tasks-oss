// Plain-text table rendering. The rules are in SPEC.md.

export type Align = "left" | "right" | "center";

export interface TableOptions {
  maxWidth?: number;
  align?: Align[];
  header?: boolean;
}

const WIDE: ReadonlyArray<readonly [number, number]> = [
  [0x1100, 0x115f], [0x2e80, 0x303e], [0x3041, 0x33ff], [0x3400, 0x4dbf],
  [0x4e00, 0x9fff], [0xa000, 0xa4cf], [0xac00, 0xd7a3], [0xf900, 0xfaff],
  [0xfe30, 0xfe4f], [0xff00, 0xff60], [0xffe0, 0xffe6], [0x1f300, 0x1f64f],
  [0x1f900, 0x1f9ff], [0x20000, 0x3fffd],
];

const ALIGNS: ReadonlySet<string> = new Set(["left", "right", "center"]);

function charWidth(ch: string): number {
  const cp = ch.codePointAt(0)!;
  for (const [lo, hi] of WIDE) if (cp >= lo && cp <= hi) return 2;
  return 1;
}

export function displayWidth(text: string): number {
  let w = 0;
  for (const ch of text) w += charWidth(ch);
  return w;
}

function words(paragraph: string): string[] {
  return paragraph.split(" ").filter((w) => w.length > 0);
}

function wrapParagraph(paragraph: string, width: number): string[] {
  const lines: string[] = [];
  let line = "";
  let lineWidth = 0;
  for (const word of words(paragraph)) {
    const ww = displayWidth(word);
    if (line.length > 0 && lineWidth + 1 + ww <= width) {
      line += " " + word;
      lineWidth += 1 + ww;
      continue;
    }
    if (line.length === 0 && ww <= width) {
      line = word;
      lineWidth = ww;
      continue;
    }
    if (line.length > 0) lines.push(line);
    line = "";
    lineWidth = 0;
    if (ww <= width) {
      line = word;
      lineWidth = ww;
      continue;
    }
    for (const ch of word) {
      const cw = charWidth(ch);
      if (lineWidth + cw > width) {
        lines.push(line);
        line = "";
        lineWidth = 0;
      }
      line += ch;
      lineWidth += cw;
    }
  }
  lines.push(line);
  return lines;
}

function pad(text: string, width: number, align: Align): string {
  const extra = width - displayWidth(text);
  if (align === "right") return " ".repeat(extra) + text;
  if (align === "center") {
    const left = Math.floor(extra / 2);
    return " ".repeat(left) + text + " ".repeat(extra - left);
  }
  return text + " ".repeat(extra);
}

export function renderTable(rows: string[][], options: TableOptions = {}): string {
  const { maxWidth, align = [], header = false } = options;
  if (maxWidth !== undefined && (!Number.isInteger(maxWidth) || maxWidth < 1)) {
    throw new RangeError(`maxWidth must be a positive integer, got ${maxWidth}`);
  }
  for (const a of align) {
    if (!ALIGNS.has(a)) throw new RangeError(`unknown alignment ${String(a)}`);
  }
  const columns = rows.reduce((n, row) => Math.max(n, row.length), 0);
  if (columns === 0) return "";
  const cell = (row: string[], c: number) => (c < row.length ? row[c] : "");

  const widths: number[] = [];
  const minimums: number[] = [];
  for (let c = 0; c < columns; c++) {
    let natural = 0;
    let minimum = 1;
    for (const row of rows) {
      const text = cell(row, c);
      for (const paragraph of text.split("\n")) {
        natural = Math.max(natural, displayWidth(words(paragraph).join(" ")));
      }
      for (const ch of text) if (charWidth(ch) === 2) minimum = 2;
    }
    minimums.push(minimum);
    widths.push(Math.max(natural, minimum));
  }

  const total = () => widths.reduce((a, b) => a + b, 0) + 3 * (columns - 1);
  if (maxWidth !== undefined) {
    while (total() > maxWidth) {
      let pick = -1;
      for (let c = 0; c < columns; c++) {
        if (widths[c] > minimums[c] && (pick === -1 || widths[c] >= widths[pick])) pick = c;
      }
      if (pick === -1) throw new RangeError(`table cannot fit in ${maxWidth} columns`);
      widths[pick] -= 1;
    }
  }

  const out: string[] = [];
  rows.forEach((row, r) => {
    const cellLines: string[][] = [];
    for (let c = 0; c < columns; c++) {
      cellLines.push(cell(row, c).split("\n").flatMap((p) => wrapParagraph(p, widths[c])));
    }
    const height = Math.max(...cellLines.map((l) => l.length));
    for (let i = 0; i < height; i++) {
      out.push(cellLines.map((lines, c) => pad(lines[i] ?? "", widths[c], align[c] ?? "left")).join(" | "));
    }
    if (header && r === 0) out.push(widths.map((w) => "-".repeat(w)).join("-+-"));
  });
  return out.join("\n");
}
