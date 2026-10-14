import { defaultLayout } from "./layout.js";
import { renderMarkdown } from "./markdown.js";

const HOOKS = ["beforeRender", "afterRender", "onComplete"];

/** "guide/intro.md" -> "guide/intro.html" */
export function outputPath(sourcePath) {
  return sourcePath.replace(/\.md$/, "") + ".html";
}

export class PluginError extends Error {
  constructor(plugin, hook, cause) {
    super(`plugin "${plugin}" failed in ${hook}: ${cause?.message ?? cause}`, { cause });
    this.name = "PluginError";
    this.plugin = plugin;
    this.hook = hook;
  }
}

async function callHook(plugin, hook, args) {
  try {
    return await plugin[hook](...args);
  } catch (err) {
    throw new PluginError(plugin.name, hook, err);
  }
}

/** A site with plugin hooks; see docs/plugins.md. */
export function createSite({ layout = defaultLayout } = {}) {
  const plugins = [];

  const site = {
    use(plugin) {
      if (plugin === null || typeof plugin !== "object") {
        throw new TypeError("a plugin must be an object");
      }
      if (typeof plugin.name !== "string" || plugin.name === "") {
        throw new TypeError("a plugin needs a non-empty string name");
      }
      for (const hook of HOOKS) {
        if (plugin[hook] !== undefined && typeof plugin[hook] !== "function") {
          throw new TypeError(`plugin "${plugin.name}": ${hook} must be a function`);
        }
      }
      if (plugins.some((p) => p.name === plugin.name)) {
        throw new Error(`a plugin named "${plugin.name}" is already registered`);
      }
      plugins.push(plugin);
      return site;
    },

    async build(pages) {
      const outputs = new Map();
      for (const original of pages) {
        let page = { ...original };
        for (const plugin of plugins) {
          if (!plugin.beforeRender) continue;
          const result = await callHook(plugin, "beforeRender", [page]);
          if (result === undefined) continue;
          if (result === null || typeof result !== "object") {
            throw new PluginError(plugin.name, "beforeRender", new TypeError("beforeRender must return a page object or undefined"));
          }
          page = result;
        }
        const content = renderMarkdown(page.body);
        let html = layout({ title: page.title, content, path: page.path });
        for (const plugin of plugins) {
          if (!plugin.afterRender) continue;
          const result = await callHook(plugin, "afterRender", [html, page]);
          if (result === undefined) continue;
          if (typeof result !== "string") {
            throw new PluginError(plugin.name, "afterRender", new TypeError("afterRender must return a string or undefined"));
          }
          html = result;
        }
        outputs.set(outputPath(page.path), html);
      }
      for (const plugin of plugins) {
        if (plugin.onComplete) await callHook(plugin, "onComplete", [outputs]);
      }
      return outputs;
    },
  };
  return site;
}

/**
 * Render every page. Pages are { path, title, body }; the result maps each
 * output path to its HTML, in page order.
 */
export async function buildSite(pages, options = {}) {
  return createSite(options).build(pages);
}
