# Task plan (fixed before authoring)

Fifty tasks: 20 easy, 20 medium, 10 hard, across nine categories, with each
category spanning more than one difficulty so the category does not give the
difficulty away. 22 Python, 18 TypeScript, 10 JavaScript.

| # | id | category | difficulty | language | what the task asks for |
|---|----|----------|------------|----------|------------------------|
| 1 | py-chunk-evenly | utility | easy | python | `chunk_evenly(items, n)`: n consecutive chunks, sizes differ by at most one, longer first, empty extras, ValueError for n < 1. |
| 2 | ts-clamp-range | utility | easy | typescript | `clamp(value, min, max)` and Python-style `range(start, stop?, step?)` with negative steps; RangeError for step 0 and for min > max. |
| 3 | js-pick-omit | utility | easy | javascript | `pick(obj, keys)` / `omit(obj, keys)`: own enumerable keys only, missing keys ignored, inputs not mutated. |
| 4 | py-retry-backoff | utility | medium | python | `retry(fn, attempts, base_delay, max_delay, retry_on, sleep)` with capped exponential backoff, re-raising the last error, never retrying non-matching exceptions; injected sleep. |
| 5 | ts-deep-merge | utility | medium | typescript | `deepMerge(target, ...sources)` returning a new object; plain objects merge recursively, arrays replace or concatenate by option, `undefined` never overwrites, `__proto__`/`constructor`/`prototype` keys ignored, class instances and Dates copied by reference. |
| 6 | py-cron-next | utility | hard | python | `next_run(expr, after)` for five-field cron: lists, ranges, steps, names, Sunday as 0 or 7, day-of-month/day-of-week OR rule, strictly after `after`, ValueError for invalid or never-matching expressions. |
| 7 | py-format-phone | formatting | easy | python | `format_us_phone(raw)`: digits only, 10 digits or 11 with a leading 1, `(415) 555-0123`, ValueError otherwise. |
| 8 | ts-format-money | formatting | easy | typescript | `formatCents(cents, currency)`: thousands separators, two decimals, `$`/`€`/`£`, a leading minus for negatives, TypeError for non-integers. |
| 9 | js-pluralize | formatting | easy | javascript | `pluralize(count, singular, plural?)`: "1 file", "0 files", default plural rules for s/x/z/ch/sh and consonant + y. |
| 10 | py-flatten-records-csv | formatting | medium | python | `records_to_csv(records)`: nested dicts to dot-path columns in first-seen order, lists joined with `;`, missing cells empty, proper CSV quoting. |
| 11 | js-human-duration | formatting | medium | javascript | `formatDuration(ms, options)`: largest N non-zero units, long and compact styles, singular/plural, zero and invalid input rules. |
| 12 | ts-table-wrap | formatting | hard | typescript | `renderTable(rows, options)`: fit a maximum width by shrinking the widest columns, wrap on words, break long words, per-column alignment, display width 2 for wide East Asian characters (spec in the workspace). |
| 13 | py-parse-kv | parsing | easy | python | `parse_kv("a=1; b = two")`: trimmed pairs, empty segments skipped, last duplicate wins, ValueError for a segment without `=`. |
| 14 | ts-parse-clock | parsing | easy | typescript | `parseClock("7:30 pm")` to minutes after midnight: 24-hour and 12-hour forms, 12am/12pm rules, errors for out-of-range input. |
| 15 | js-parse-ini | parsing | medium | javascript | `parseIni(text)`: sections, comments, quoted values with escapes, line continuation, merged duplicate sections, SyntaxError carrying the line number. |
| 16 | py-parse-query | parsing | medium | python | `parse_query` / `build_query`: percent-decoding, `+` as space, repeated keys, bare keys, malformed escapes kept, round trip. |
| 17 | ts-semver-range | parsing | medium | typescript | `satisfies(version, range)`: exact, comparison operators, `^`, `~`, hyphen ranges, x-ranges and `||` (no prereleases). |
| 18 | py-expr-eval | parsing | hard | python | Tokenizer, parser and evaluator for arithmetic with variables, functions, right-associative `^`, unary minus below `^`, and `ExprError` carrying the character position. |
| 19 | py-validate-username | validation | easy | python | `is_valid_username(name)`: length, first character, allowed characters, no doubled or trailing separators. |
| 20 | ts-hex-color | validation | easy | typescript | `normalizeHexColor(input)`: 3, 4, 6 or 8 digits with `#`, expanded and lowercased, `null` when invalid. |
| 21 | js-email-list | validation | easy | javascript | `parseEmailList(text)`: split on commas, semicolons and whitespace, valid vs invalid by stated rules, case-insensitive de-duplication keeping the first spelling. |
| 22 | py-card-iban | validation | medium | python | `card_brand(number)` with the Luhn check and brand prefixes/lengths, and `is_valid_iban(iban)` with mod-97 and a country length table. |
| 23 | ts-signup-validate | validation | medium | typescript | `validateSignup(input, today)`: one error code per field in a stated priority, trimming, password rules, age from an injected date. |
| 24 | ts-schema-validator | validation | hard | typescript | A JSON-Schema subset validator (types, required, properties, additionalProperties, enum, const, ranges, lengths in code points, pattern, items, uniqueItems, local `$ref`, oneOf/anyOf/allOf) returning JSON-pointer error paths (spec in the workspace). |
| 25 | py-shared-default-tags | bugfix | easy | python | Tags from one call leak into the next (a mutable default argument). |
| 26 | ts-paginate-off-by-one | bugfix | easy | typescript | `paginate` returns the wrong slice and page count at the boundaries. |
| 27 | js-score-sort | bugfix | easy | javascript | The leaderboard sorts scores as strings; numeric descending with name as tie-break. |
| 28 | py-weekly-report-bugs | bugfix | medium | python | Weekly buckets are wrong around New Year (ISO weeks) and the report drops its last page; two bugs in two files, symptoms only. |
| 29 | ts-emitter-bugs | bugfix | medium | typescript | An event emitter where `off()` cannot remove a `once` listener, removing a listener during emit skips the next one, and listeners added during emit run too early. |
| 30 | js-debounce-bugs | bugfix | medium | javascript | `debounce` with leading/trailing/maxWait and an injected scheduler: stale trailing arguments, double calls, `cancel()` not cancelling. |
| 31 | py-inventory-reservations | bugfix | hard | python | A multi-file reservation service with several interacting bugs (expired holds still counted, double release, confirming after expiry, non-idempotent retries), reported as customer symptoms. |
| 32 | py-top-n-reverse | api-change | easy | python | Add keyword-only `reverse=False` to `top_n` without breaking callers; ValueError for negative n. |
| 33 | ts-notify-many | api-change | easy | typescript | `notify` accepts a string or an array, de-duplicates, returns how many were sent; existing callers unchanged. |
| 34 | js-client-options | api-change | medium | javascript | `createClient` moves from positional arguments to an options object with defaults, keeps the old form working with one deprecation warning, and its three callers are updated. |
| 35 | py-user-stats-dataclass | api-change | medium | python | `get_user_stats` returns a `UserStats` dataclass that still unpacks like the old tuple; callers in two modules updated. |
| 36 | py-cursor-pagination | api-change | hard | python | Offset pagination becomes opaque-cursor pagination across repository, service and API layers: stable order under ties and inserts, filters, invalid-cursor errors, the old function kept as a deprecated wrapper. |
| 37 | js-cli-json-flag | feature | easy | javascript | Add `--json` output to a two-file CLI. |
| 38 | py-report-csv-export | feature | medium | python | Add a CSV exporter to a reporting package, register it, and expose it on the command line with stated number formatting. |
| 39 | ts-todo-query | feature | medium | typescript | Filtering and sorting for a todo service and its query-string handler (status, tag, text, due date, nulls last, tie-breaks). |
| 40 | js-site-plugins | feature | medium | javascript | Plugin hooks for a small static-site renderer: registration order, async hooks, errors naming the plugin. |
| 41 | ts-undo-redo | feature | hard | typescript | Undo/redo for an editor model across three files: transactions, merging adjacent typing within one second (injected clock), redo cleared by new edits, history limit, selection restored. |
| 42 | py-shipping-constants | refactor | easy | python | Rename `calc` to `shipping_cost` (keeping a deprecated alias) and replace magic numbers with named constants; behaviour unchanged. |
| 43 | ts-config-promise | refactor | easy | typescript | `readConfig` moves from a callback to a Promise while a passed callback keeps working. |
| 44 | py-extract-validators | refactor | medium | python | Duplicated validation in two modules moves into `validators.py` with stated function names; both modules use it; behaviour unchanged. |
| 45 | ts-pricing-rules | refactor | hard | typescript | A monolithic order-total function becomes an ordered rule pipeline, and a bundle discount is added that interacts with coupon exclusivity and per-line rounding (spec in the workspace). |
| 46 | py-memoize | state | easy | python | A `memoize` decorator with `cache_info()` and `cache_clear()`. |
| 47 | ts-weighted-lru | state | medium | typescript | An LRU cache bounded by total weight: `peek` without touching recency, oversize items rejected, eviction callback, hit/miss/eviction stats. |
| 48 | py-order-state-machine | state | medium | python | An order lifecycle state machine: transition table, guards, terminal states, history with injected timestamps, `InvalidTransition`. |
| 49 | ts-singleflight-cache | state | hard | typescript | An async cache with TTL, stale-while-revalidate, request coalescing, failed loads not cached but stale values served within the window, LRU limit, injected clock. |
| 50 | py-async-rate-limiter | state | hard | python | An asyncio per-key token bucket with burst, a global concurrency cap, FIFO fairness per key and cancellation safety, tested with an injected clock. |
