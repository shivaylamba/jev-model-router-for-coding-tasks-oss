import { defaultLayout } from "./layout.js";
import { renderMarkdown } from "./markdown.js";

/** "guide/intro.md" -> "guide/intro.html" */
export function outputPath(sourcePath) {
  return sourcePath.replace(/\.md$/, "") + ".html";
}

/**
 * Render every page. Pages are { path, title, body }; the result maps each
 * output path to its HTML, in page order.
 */
export async function buildSite(pages, { layout = defaultLayout } = {}) {
  const outputs = new Map();
  for (const page of pages) {
    const content = renderMarkdown(page.body);
    outputs.set(outputPath(page.path), layout({ title: page.title, content, path: page.path }));
  }
  return outputs;
}
