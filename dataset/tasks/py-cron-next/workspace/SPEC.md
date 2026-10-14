# Cron expressions supported by minicron

## `next_run(expr, after)`

`next_run(expr: str, after: datetime) -> datetime` returns the earliest minute
that matches `expr` and is **strictly after** `after`. The result always has
`second == 0` and `microsecond == 0` and carries the same `tzinfo` as `after`
(arithmetic is plain wall-clock time; there is no DST handling).

Examples: `next_run("* * * * *", 10:00:30)` is 10:01:00, and
`next_run("30 9 * * *", 09:30:00)` is 09:30 on the *next* day.

## Fields

An expression has exactly five fields separated by one or more spaces or tabs.
Leading and trailing whitespace is ignored.

| field        | allowed values | names                     |
|--------------|----------------|---------------------------|
| minute       | 0-59           |                           |
| hour         | 0-23           |                           |
| day of month | 1-31           |                           |
| month        | 1-12           | `JAN` ... `DEC`           |
| day of week  | 0-7            | `SUN` ... `SAT`           |

In the day-of-week field both 0 and 7 mean Sunday, so `5-7` is Friday,
Saturday and Sunday.

Names are three-letter English abbreviations, case-insensitive (`MON`, `mon`,
`Mon`). They may be used wherever a number is allowed for that field (single
values and the ends of ranges), but never as a step.

## Items

A field is a comma-separated list of one or more items, with no spaces. An item
is one of:

| item    | meaning                                                         |
|---------|-----------------------------------------------------------------|
| `*`     | every allowed value                                             |
| `N`     | the single value N                                              |
| `A-B`   | A through B inclusive; A must not be greater than B (no wrap)   |
| `*/S`   | every S-th value starting at the field's minimum                |
| `A-B/S` | every S-th value from A, up to and including B if reached       |
| `N/S`   | every S-th value from N up to the field's maximum               |

S must be a positive integer. So `*/15` in the minute field is 0, 15, 30, 45;
`*/2` in the day-of-month field is 1, 3, 5, ..., 31; `5/20` in the minute
field is 5, 25, 45; `9-17/4` in the hour field is 9, 13, 17.

## Macros

Instead of five fields, the whole expression may be one of these macros
(case-insensitive, surrounding whitespace ignored):

| macro                    | equivalent    |
|--------------------------|---------------|
| `@yearly`, `@annually`   | `0 0 1 1 *`   |
| `@monthly`               | `0 0 1 * *`   |
| `@weekly`                | `0 0 * * 0`   |
| `@daily`, `@midnight`    | `0 0 * * *`   |
| `@hourly`                | `0 * * * *`   |

## Day of month vs day of week

A field is *unrestricted* when its text starts with `*` (for example `*` or
`*/2`); otherwise it is restricted.

- If both the day-of-month and day-of-week fields are restricted, a day matches
  when it matches **either** field. `0 0 13 * FRI` runs on every 13th and on
  every Friday.
- Otherwise a day must match **both** fields. With `*` that is the same as
  ignoring the field, but `0 0 */2 * MON` runs only on Mondays that fall on an
  odd day of the month.

The month field always applies.

## Errors

`next_run` raises `ValueError` for:

- a wrong number of fields or an unknown macro;
- an empty item (`1,,2`), an unknown name, anything that is not a number or a
  name where a value is expected, or a name used as a step;
- a value outside the field's allowed range, a range whose start is greater
  than its end, or a step that is zero or not a positive integer;
- an expression that has no matching time within eight years after `after`.
  This is how impossible dates such as `0 0 30 2 *` (February 30th) are
  reported. February 29th is a real date and must be found even when the next
  leap year is several years away (remember 2100 is not a leap year).
