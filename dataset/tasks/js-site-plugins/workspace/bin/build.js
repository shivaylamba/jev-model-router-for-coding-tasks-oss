#!/usr/bin/env node
import { mkdir, readdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join, relative } from "node:path";
import { buildSite } from "../src/site.js";

async function collect(dir, root = dir) {
  const pages = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) pages.push(...(await collect(full, root)));
    else if (entry.name.endsWith(".md")) {
      const body = await readFile(full, "utf8");
      const title = /^#\s+(.*)$/m.exec(body)?.[1] ?? entry.name;
      pages.push({ path: relative(root, full), title, body });
    }
  }
  return pages;
}

const [source = "content", target = "out"] = process.argv.slice(2);
const outputs = await buildSite(await collect(source));
for (const [path, html] of outputs) {
  await mkdir(dirname(join(target, path)), { recursive: true });
  await writeFile(join(target, path), html);
}
console.log(`wrote ${outputs.size} pages to ${target}`);
