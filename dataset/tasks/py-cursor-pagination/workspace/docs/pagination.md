# Cursor pagination for article listings

Status: agreed, to be implemented. Replaces offset paging (`page` / `per_page`),
which shows duplicates and skips articles when articles are published while a
client is paging, and returns ties in an arbitrary order.

## Order

Every listing (cursor and legacy offset) is ordered by `published_at`
descending, then by `id` descending for articles with the same `published_at`.

## Service: `ArticleService.list_articles(limit=20, cursor=None, author=None, status=None)`

Returns a `Page` (a dataclass defined in `articles/service.py`) with:

- `items`: list of `Article`, at most `limit` of them, in the order above;
- `next_cursor`: a `str` to pass as `cursor` for the following page, or `None`
  when there are no more matching articles after the last item returned.
  A non-`None` `next_cursor` therefore never leads to an empty page unless
  articles were deleted in between.

Parameters:

- `limit`: an `int` from 1 to 100 (`bool` is not accepted); otherwise `ValidationError`.
- `status`: `None` or one of `draft`, `published`, `archived`; otherwise `ValidationError`.
- `author`: `None` or an author name, matched exactly.
- `cursor`: `None` for the first page, or a `next_cursor` from an earlier call.

Cursor rules:

- Cursors are opaque strings made only of ASCII letters, digits, `-` and `_`.
  Clients must not parse them.
- A cursor marks a position in the order (the last item of the page it came
  from), not an offset. The next page contains the matching articles that sort
  strictly after that position. Consequences:
  - articles inserted that sort before the position (newer, or same
    `published_at` with a higher id) never show up in later pages and never
    push already-seen articles into them;
  - articles inserted that sort after the position appear in later pages;
  - deleting the article a cursor points at does not break the cursor.
- A cursor remembers the `author` and `status` filters it was created with.
  Using it with different filter values raises `InvalidCursorError`.
  `limit` may change from one request to the next.
- Any string that is not a cursor produced by `list_articles` (including the
  empty string and well-formed base64 that does not decode to a cursor) raises
  `InvalidCursorError`, never a different exception and never a page.

`InvalidCursorError` lives in `articles/errors.py` and subclasses `ValidationError`.

## Legacy: `ArticleService.list_page(page, per_page, author, status)`

Kept for existing callers, with the same parameters, validation and return
value as today, but every call emits a `DeprecationWarning` (via
`warnings.warn`) pointing to `list_articles`. Its items use the order above.

## API: `ArticlesApi.handle_list(params)`

`params` maps query-string names to string values.

- Cursor mode (the default): parameters `limit` (decimal digits only, default
  20), `cursor`, `author`, `status`. An empty `cursor` value is the same as no
  cursor. Response: `200, {"items": [...], "next_cursor": str or None}` with
  items serialized by `serialize()`.
- Legacy mode: when `page` or `per_page` is present. Same response as today
  (`items`, `page`, `per_page`, `total`), produced through `list_page`.
- Sending `page` or `per_page` together with `cursor` or `limit` is a 400.
- Any `ValidationError` (including `InvalidCursorError`) is a
  `400, {"error": message}` response.
