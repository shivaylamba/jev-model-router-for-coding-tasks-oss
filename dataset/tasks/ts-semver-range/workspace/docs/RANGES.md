# Version ranges

The registry only publishes release versions `MAJOR.MINOR.PATCH` (see
`parseVersion` in `src/semver.ts`). There are no prerelease or build tags, and
a version string containing one is invalid.

A range is one or more **alternatives** separated by `||`. A version satisfies
the range if it satisfies any alternative. Whitespace around `||` is ignored.

An alternative is either

- a **hyphen range** `A - B` (whitespace on both sides of the `-` is
  required), or
- zero or more **comparators** separated by whitespace, all of which must hold.
  An empty alternative (for example the whole range `""`, or the right side
  of `1.0.0 ||`) matches every version.

## Partial versions

Wherever a version appears in a range it may be partial: `1`, `1.2` or
`1.2.3`. Each part is a non-negative integer without leading zeros (`0` is
fine, `01` is not), or one of the wildcards `x`, `X` or `*`. Once a part is a
wildcard, the remaining parts must be wildcards or left out (`1.x.x` and `1.x`
are fine, `1.x.3` is invalid). A missing part counts as a wildcard, so `1.2`
means the same as `1.2.x`. A leading `v` is allowed on any version (`v1.2.3`).

## Comparators

A comparator is an optional operator followed by a partial version. Whitespace
is allowed between the operator and the version (`>= 1.2.3`).

| Comparator | Meaning |
|---|---|
| `1.2.3` or `=1.2.3` | exactly `1.2.3` |
| `1.2` / `1.2.x` / `=1.2` | `>=1.2.0 <1.3.0` |
| `1` / `1.x` / `1.x.x` | `>=1.0.0 <2.0.0` |
| `*`, `x`, `X` (alone, with or without `=`) | any version |
| `>1.2.3`, `>=1.2.3`, `<1.2.3`, `<=1.2.3` | the usual comparison |
| `>1.2` | `>=1.3.0` (greater than everything `1.2.x` covers) |
| `>1` | `>=2.0.0` |
| `>=1.2` | `>=1.2.0` |
| `<1.2` | `<1.2.0` |
| `<=1.2` | `<1.3.0` (everything up to and including `1.2.x`) |
| `<=1` | `<2.0.0` |
| `>*`, `<*` | no version |
| `>=*`, `<=*` | any version |
| `~1.2.3` | `>=1.2.3 <1.3.0` |
| `~1.2` | `>=1.2.0 <1.3.0` |
| `~1` | `>=1.0.0 <2.0.0` |
| `^1.2.3` | `>=1.2.3 <2.0.0` |
| `^0.2.3` | `>=0.2.3 <0.3.0` |
| `^0.0.3` | `>=0.0.3 <0.0.4` |
| `^1.2` | `>=1.2.0 <2.0.0` |
| `^0.2` | `>=0.2.0 <0.3.0` |
| `^0.0` | `>=0.0.0 <0.1.0` |
| `^1` / `^1.x` | `>=1.0.0 <2.0.0` |
| `^0` / `^0.x` | `>=0.0.0 <1.0.0` |
| `~*`, `^*` | any version |

In words: `^` allows changes that do not modify the left-most non-zero part
among the parts given; `~` allows patch-level changes when a minor version is
given and minor-level changes otherwise.

## Hyphen ranges

`A - B` means `>=A <=B`, where both sides may be partial:

- A partial lower bound is filled with zeros: `1.2 - 2.3.4` is
  `>=1.2.0 <=2.3.4`. A lower bound of `*` means no lower bound.
- A partial upper bound includes everything it covers: `1.2.3 - 2.3` is
  `>=1.2.3 <2.4.0`, `1.2.3 - 2` is `>=1.2.3 <3.0.0`. An upper bound of `*`
  means no upper bound.
- Operators are not allowed inside a hyphen range.

## Invalid ranges

Anything that does not fit the grammar above is invalid, for example
`>=1.2.3.4`, `~>1.2`, `1.2.3 -`, `>=`, `1.x.3`, `01.2.3`, `1.2.3-beta`,
`abc`, `1.2.3 - 2.0.0 - 3.0.0`.
