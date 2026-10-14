# pagesmith

A small static-site generator for our docs: Markdown-ish pages in, HTML out.

```
node bin/build.js content out
```

- `src/markdown.js`: the tiny Markdown subset we support (headings, paragraphs, `**bold**`, `` `code` ``, `[links](url)`)
- `src/layout.js`: the default HTML layout
- `src/site.js`: `buildSite(pages, options)`; pages are `{ path, title, body }`
  objects and the result is a `Map` from output path (`about.md` -> `about.html`)
  to HTML
- `bin/build.js`: reads a content directory and writes the output directory
- `docs/`: design notes

Node 24, no dependencies. Run the tests with `node --test`.
