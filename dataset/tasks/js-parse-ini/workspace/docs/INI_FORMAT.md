# INI format

This is the dialect `stringifyIni` writes and `parseIni` reads.

## Lines

- Files use `\n` or `\r\n` line endings. Lines are numbered from 1.
- Each line is trimmed of leading and trailing whitespace before it is looked at.
- Blank lines are ignored.
- A line whose first character is `;` or `#` is a comment and is ignored.
  There are no inline comments: a `;` or `#` later in a line is ordinary text.

## Sections

- `[name]` starts a section. The name is the text between the brackets,
  trimmed. It is kept as written (a dot in `[server.http]` is just part of
  the name, not nesting).
- An empty name (`[]`, `[  ]`) or a line that starts with `[` but does not
  end with `]` is a syntax error.
- A section that appears more than once is one section: its keys are merged.
- A section with no keys still appears in the result, as an empty object.
- Keys that appear before the first section header belong to the section
  named `""` (empty string). That section appears in the result only if it
  has at least one key.

## Keys and values

- `key = value`: the line is split on its first `=`. Key and value are trimmed.
- An empty key is a syntax error. An empty value is allowed.
- If a key appears more than once in the same section, the last value wins.
- Any other non-blank, non-comment line (no `=` and not a section header) is
  a syntax error.

## Quoted values

- If a value (after trimming) starts with `"`, it is a quoted string. The
  value is the text between the quotes, with these escapes:
  `\"` (quote), `\\` (backslash), `\n` (newline), `\t` (tab).
- Whitespace inside the quotes is kept.
- Any other escape, a missing closing quote, or anything other than
  whitespace after the closing quote is a syntax error.
- Quoted values never continue onto the next line.

## Line continuation

- If an unquoted value ends with a backslash, the value continues on the next
  line: the backslash is removed, the value is trimmed at the end, and the
  next line (trimmed) is appended after a single space. The next line is always
  taken as continuation text, even if it starts with `[`, `;` or `#`, and it
  can itself end with a backslash to continue further.
- A continuation backslash on the last line of the file is a syntax error.

## Result

`parseIni` returns a plain object whose keys are section names, in the order
the sections first appear, and whose values are plain objects mapping keys to
string values.

## Errors

Syntax errors are thrown as a `SyntaxError` with a numeric `line` property
holding the 1-based number of the offending line. For an unterminated
continuation, that is the line with the trailing backslash.
