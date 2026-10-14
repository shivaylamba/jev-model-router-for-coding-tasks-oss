import { test } from "node:test";
import assert from "node:assert/strict";
import { buildSite, createSite, PluginError } from "../src/site.js";

const plain = { layout: ({ title, content }) => `${title}|${content}` };
const pages = () => [
  { path: "index.md", title: "Home", body: "hello" },
  { path: "about.md", title: "About", body: "us" },
];

test("use() chains and build() works without plugins", async () => {
  const site = createSite(plain);
  assert.equal(site.use({ name: "noop" }), site);
  const outputs = await site.build(pages());
  assert.ok(outputs instanceof Map);
  assert.deepEqual([...outputs], [["index.html", "Home|<p>hello</p>"], ["about.html", "About|<p>us</p>"]]);
});

test("buildSite is unchanged", async () => {
  const outputs = await buildSite(pages(), plain);
  assert.equal(outputs.get("about.html"), "About|<p>us</p>");
});

test("hooks run in registration order, page by page", async () => {
  const log = [];
  const plugin = (name) => ({
    name,
    beforeRender: (page) => { log.push(`${name}:before:${page.path}`); },
    afterRender: (html, page) => { log.push(`${name}:after:${page.path}`); },
    onComplete: () => { log.push(`${name}:complete`); },
  });
  await createSite(plain).use(plugin("a")).use(plugin("b")).build(pages());
  assert.deepEqual(log, [
    "a:before:index.md", "b:before:index.md", "a:after:index.md", "b:after:index.md",
    "a:before:about.md", "b:before:about.md", "a:after:about.md", "b:after:about.md",
    "a:complete", "b:complete",
  ]);
});

test("beforeRender results chain and drive the path, title and body", async () => {
  const outputs = await createSite(plain)
    .use({ name: "rename", beforeRender: (page) => ({ ...page, path: `docs/${page.path}` }) })
    .use({ name: "shout", beforeRender: (page) => ({ ...page, title: page.title.toUpperCase(), body: page.body + "!" }) })
    .build(pages());
  assert.deepEqual([...outputs.keys()], ["docs/index.html", "docs/about.html"]);
  assert.equal(outputs.get("docs/index.html"), "HOME|<p>hello!</p>");
});

test("afterRender results chain; undefined keeps the HTML; final page is passed", async () => {
  const seen = [];
  const outputs = await createSite(plain)
    .use({ name: "wrap", afterRender: (html) => `[${html}]` })
    .use({ name: "keep", afterRender: (html, page) => { seen.push(page.title); } })
    .use({ name: "tag", afterRender: (html) => `${html}#` })
    .use({ name: "retitle", beforeRender: (page) => ({ ...page, title: "T" }) })
    .build(pages());
  assert.equal(outputs.get("index.html"), "[T|<p>hello</p>]#");
  assert.deepEqual(seen, ["T", "T"]);
});

test("async hooks are awaited in order", async () => {
  const log = [];
  const delay = () => new Promise((resolve) => setImmediate(resolve));
  const outputs = await createSite(plain)
    .use({ name: "slow", beforeRender: async (page) => { await delay(); log.push("slow"); return { ...page, title: "S" }; } })
    .use({ name: "fast", beforeRender: (page) => { log.push(`fast:${page.title}`); } })
    .use({ name: "after", afterRender: async (html) => { await delay(); return html + "~"; } })
    .build([pages()[0]]);
  assert.deepEqual(log, ["slow", "fast:S"]);
  assert.equal(outputs.get("index.html"), "S|<p>hello</p>~");
});

test("onComplete can add entries and build waits for it", async () => {
  const outputs = await createSite(plain)
    .use({
      name: "sitemap",
      onComplete: async (map) => {
        await new Promise((resolve) => setImmediate(resolve));
        map.set("sitemap.txt", [...map.keys()].join("\n"));
      },
    })
    .build(pages());
  assert.equal(outputs.get("sitemap.txt"), "index.html\nabout.html");
});

test("the caller's page objects are not mutated", async () => {
  const input = pages();
  await createSite(plain).use({ name: "mutator", beforeRender: (page) => { page.title = "changed"; } }).build(input);
  assert.equal(input[0].title, "Home");
});

test("use() validation", () => {
  const site = createSite(plain);
  assert.throws(() => site.use(null), TypeError);
  assert.throws(() => site.use("seo"), TypeError);
  assert.throws(() => site.use({}), TypeError);
  assert.throws(() => site.use({ name: "" }), TypeError);
  assert.throws(() => site.use({ name: "x", afterRender: "nope" }), TypeError);
  site.use({ name: "dup", extra: 1 });
  assert.throws(() => site.use({ name: "dup" }), Error);
});

test("a throwing hook becomes a PluginError and stops the build", async () => {
  const boom = new Error("boom");
  let completed = false;
  let laterRan = false;
  const site = createSite(plain)
    .use({ name: "first", afterRender: () => { throw boom; } })
    .use({ name: "second", afterRender: () => { laterRan = true; }, onComplete: () => { completed = true; } });
  await assert.rejects(site.build(pages()), (err) => {
    assert.ok(err instanceof PluginError);
    assert.ok(err instanceof Error);
    assert.equal(err.plugin, "first");
    assert.equal(err.hook, "afterRender");
    assert.equal(err.cause, boom);
    assert.ok(err.message.includes("first"));
    return true;
  });
  assert.equal(laterRan, false);
  assert.equal(completed, false);
});

test("a rejected promise names the plugin and hook", async () => {
  const site = createSite(plain).use({ name: "checker", onComplete: async () => { throw new RangeError("bad link"); } });
  await assert.rejects(site.build(pages()), (err) => err instanceof PluginError && err.plugin === "checker" && err.hook === "onComplete" && err.cause instanceof RangeError);
});

test("wrong return types become PluginErrors with a TypeError cause", async () => {
  const before = createSite(plain).use({ name: "badpage", beforeRender: () => "not a page" });
  await assert.rejects(before.build(pages()), (err) => err instanceof PluginError && err.plugin === "badpage" && err.hook === "beforeRender" && err.cause instanceof TypeError);
  const after = createSite(plain).use({ name: "badhtml", afterRender: () => 42 });
  await assert.rejects(after.build(pages()), (err) => err instanceof PluginError && err.plugin === "badhtml" && err.hook === "afterRender" && err.cause instanceof TypeError);
});
