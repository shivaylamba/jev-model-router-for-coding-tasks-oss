import { test } from "node:test";
import assert from "node:assert/strict";
import { buildSite, outputPath } from "../src/site.js";
import { renderMarkdown } from "../src/markdown.js";

test("markdown subset", () => {
  assert.equal(
    renderMarkdown("# Hi <you>\n\nSome **bold**\nand `code` and [a link](x.html)."),
    '<h1>Hi &lt;you&gt;</h1>\n<p>Some <strong>bold</strong> and <code>code</code> and <a href="x.html">a link</a>.</p>',
  );
});

test("output paths", () => {
  assert.equal(outputPath("guide/intro.md"), "guide/intro.html");
});

test("buildSite renders every page in order", async () => {
  const outputs = await buildSite([
    { path: "index.md", title: "Home", body: "# Home" },
    { path: "about.md", title: "About", body: "About us." },
  ]);
  assert.deepEqual([...outputs.keys()], ["index.html", "about.html"]);
  assert.match(outputs.get("about.html"), /<title>About<\/title>/);
  assert.match(outputs.get("about.html"), /<p>About us.<\/p>/);
});

test("custom layout", async () => {
  const outputs = await buildSite([{ path: "a.md", title: "A", body: "x" }], {
    layout: ({ title, content }) => `${title}|${content}`,
  });
  assert.equal(outputs.get("a.html"), "A|<p>x</p>");
});
