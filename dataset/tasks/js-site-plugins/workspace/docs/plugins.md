# Plugins (agreed design, not built yet)

We want plugins for things like a sitemap, reading-time badges and link checks
without touching `site.js` every time.

## API

`createSite(options?)` (exported from `src/site.js`) returns a site object.
`options` is the same as for `buildSite` (`{ layout }`).

- `site.use(plugin)` registers a plugin and returns the site, so calls chain.
- `site.build(pages)` returns a promise of the same `Map` that `buildSite` returns.

`buildSite(pages, options)` keeps working exactly as before; it is equivalent
to `createSite(options).build(pages)` with no plugins.

## Plugins

A plugin is an object with a `name` and any of these optional hooks:

| hook | called | arguments | return value |
|------|--------|-----------|--------------|
| `beforeRender` | for each page, before rendering | `(page)` | a page object to use instead, or `undefined` to keep the page it was given |
| `afterRender` | for each page, after the layout is applied | `(html, page)` | a string to use instead, or `undefined` to keep the HTML it was given |
| `onComplete` | once, after all pages | `(outputs)` (the `Map`) | ignored; the hook may add, change or delete entries of `outputs` |

`use()` validation, all `TypeError`s thrown synchronously by `use()`:

- the plugin is not an object,
- `name` is not a non-empty string,
- one of the three hook properties is present but is not a function.

Registering a second plugin with a name that is already registered throws an
`Error` as well. Other properties on the plugin object are ignored.

## Order

- Hooks run in the order the plugins were registered.
- Pages are processed one at a time in input order: for a page, every
  `beforeRender` runs (each receives the page returned by the previous one),
  then the page is rendered, then every `afterRender` runs (each receives the
  HTML returned by the previous one, plus the final page). Only then does the
  next page start.
- The output path comes from the final page's `path`, and the layout gets the
  final page's `title` and `body`, so `beforeRender` can rename or rewrite pages.
- `onComplete` hooks run after the last page, in registration order, and
  `build()` resolves with the map once they have all finished.
- Any hook may be `async`; each hook's promise is awaited before the next hook
  starts.
- The first `beforeRender` receives a shallow copy of the caller's page, so a
  plugin that mutates its argument never changes the objects passed to `build()`.

## Errors

If a hook throws or its promise rejects, `build()` rejects with a `PluginError`
(exported from `src/site.js`, a subclass of `Error`) and no further hooks run,
including `onComplete`. A `PluginError` has:

- `plugin`: the plugin's name,
- `hook`: the hook's name (`"beforeRender"`, `"afterRender"` or `"onComplete"`),
- `cause`: the original error,
- a `message` that includes the plugin's name.

A `beforeRender` that returns something other than `undefined` or an object, or
an `afterRender` that returns something other than `undefined` or a string, is
treated the same way, with a `TypeError` as the `cause`.
