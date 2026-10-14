# Table rendering

```ts
renderTable(rows: string[][], options?: TableOptions): string

type Align = "left" | "right" | "center";
interface TableOptions {
  maxWidth?: number;   // maximum line width in display columns
  align?: Align[];     // per column, default "left"
  header?: boolean;    // draw a separator under the first row, default false
}
```

## Columns

- The number of columns is the length of the longest row. Shorter rows are
  treated as if the missing cells were empty strings.
- If there are no columns (no rows, or only empty rows) the result is `""`.
- `align[i]` applies to column `i`. Missing entries mean `"left"`; extra
  entries are ignored.

## Display width

Widths are measured in terminal columns, per Unicode code point (not per
UTF-16 code unit). A code point in one of these ranges is *wide* and counts as
2; every other code point counts as 1:

```
U+1100-U+115F   U+2E80-U+303E   U+3041-U+33FF   U+3400-U+4DBF
U+4E00-U+9FFF   U+A000-U+A4CF   U+AC00-U+D7A3   U+F900-U+FAFF
U+FE30-U+FE4F   U+FF00-U+FF60   U+FFE0-U+FFE6   U+1F300-U+1F64F
U+1F900-U+1F9FF U+20000-U+3FFFD
```

## Cell text

A cell is split into *paragraphs* on `"\n"`. Each paragraph is split into
*words* on runs of spaces (U+0020); leading, trailing and repeated spaces
therefore disappear, and words are always re-joined with a single space. An
empty or all-space paragraph produces one empty line.

## Column widths

1. The *natural width* of a column is the widest paragraph (words joined by
   single spaces) of any cell in that column.
2. The *minimum width* of a column is 2 if any of its cells contains a wide
   code point, otherwise 1.
3. Each column starts at the larger of its natural and minimum width.
4. The table width is the sum of the column widths plus 3 for each gap between
   columns (the separator is `" | "`).
5. If `maxWidth` is given and the table is wider, shrink one column by 1 and
   repeat until it fits. The column to shrink is the widest column that is
   still above its minimum width; if several are equally wide, the rightmost
   of them. If every column is at its minimum width and the table still does
   not fit, throw a `RangeError`.

## Wrapping

Each paragraph is wrapped to the column width `w` greedily, word by word:

- If the word fits on the current line (with one space before it when the
  line is not empty), append it.
- Otherwise, if the word is no wider than `w`, finish the current line (when
  it is not empty) and start a new line with the word.
- Otherwise the word is wider than `w`: finish the current line (when it is
  not empty), then cut the word into pieces, each the longest prefix of the
  remaining code points that fits in `w`. Every piece but the last becomes a
  line of its own; the last piece becomes the current line, and following
  words may be appended to it.
- At the end of the paragraph, finish the current line.

A cell's lines are the lines of its paragraphs in order. Within a row, the
row's height is the largest number of lines of any of its cells; cells with
fewer lines are padded with empty lines at the bottom.

## Output

- Every cell line is padded with spaces to exactly the column width:
  `"left"` pads on the right, `"right"` on the left, and `"center"` puts
  `floor(extra / 2)` spaces on the left and the rest on the right.
- A table line is the padded cell lines joined with `" | "`. Lines are not
  trimmed, so every line is exactly the table width.
- With `header: true`, a separator line follows the lines of the first row:
  each column contributes `"-"` repeated to its width, joined with `"-+-"`.
- Lines are joined with `"\n"`, with no trailing newline.

## Errors

- `maxWidth`, when given, must be a positive integer; otherwise throw a
  `RangeError`.
- An `align` entry other than `"left"`, `"right"` or `"center"` throws a
  `RangeError`.
