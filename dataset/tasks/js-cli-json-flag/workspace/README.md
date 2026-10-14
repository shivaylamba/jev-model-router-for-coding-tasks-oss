# tally

A small `wc`-style command-line tool: counts lines, words and characters in
text files.

```
node bin/tally.js notes.txt todo.txt
```

prints one row per file and, when more than one file is given, a `total` row:

```
      3      12      80 notes.txt
      1       4      19 todo.txt
      4      16      99 total
```

Each number is right-aligned in a 7-character column followed by a space.
A file that cannot be read is reported on stderr as `tally: cannot read <path>`,
the other files are still counted, and the exit code is 1. An unknown option
prints a usage line on stderr and exits with code 2. Otherwise the exit code is 0.

Code layout: `src/count.js` does the counting, `src/cli.js` parses arguments and
prints (`run(argv, io)` takes the IO functions as parameters so it can be
tested without touching the real terminal or disk), `bin/tally.js` wires it to
the process.

Node 24, no dependencies. Run the tests with `node --test`.
