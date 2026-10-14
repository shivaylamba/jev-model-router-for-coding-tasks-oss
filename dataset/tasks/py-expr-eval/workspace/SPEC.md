# Formula language

`calc.evaluate(expr, variables=None)` evaluates one formula and returns a
`float`. Every error is raised as `calc.ExprError` (a `ValueError` subclass)
whose `position` attribute is a 0-based index into the original `expr`
string. Error message wording is not part of the contract.

## Tokens

Whitespace (spaces and tabs) between tokens is ignored.

| Token | Form |
|---|---|
| number | `digits`, `digits.digits` or `.digits`, optionally followed by an exponent `e` or `E`, an optional `+`/`-`, and digits. So `12`, `3.5`, `.5`, `1e3`, `2.5E-2`. |
| name | a letter or `_`, then letters, digits or `_` |
| operators | `+ - * / % ^` |
| punctuation | `(` `)` `,` |

- A number never includes a trailing `.` without digits: in `5.` the number is
  `5` and the `.` is an unexpected character (position 1).
- An `e` that is not followed by digits (after an optional sign) is not part
  of the number: `2e` is the number `2` followed by the name `e`, which is
  then a syntax error (two operands in a row).
- Any other character is an error at that character's position.

## Grammar and precedence

From lowest to highest precedence:

1. `+` and `-` (binary), left-associative.
2. `*`, `/` and `%`, left-associative.
3. Unary `-` and `+` (prefix, may repeat: `--2` is `2`).
4. `^` (power), right-associative: `2^3^2` is `2^(3^2)` = 512.

Unary minus binds less tightly than `^`, so `-2^2` is `-(2^2)` = -4. The
right operand of `^` is itself a unary expression, so `2^-1` is 0.5 and
`-2^-2` is -0.25.

Primary expressions are numbers, names, function calls `name(arg, ...)` and
parenthesised expressions. A name directly followed by `(` (whitespace
allowed between them) is a function call. A call has zero or more
comma-separated arguments; each argument is a full expression.

There is no implicit multiplication: `2x`, `2(3)` and `(1)(2)` are syntax
errors.

## Syntax errors and their positions

The whole formula is parsed before anything is evaluated, so a syntax error
anywhere is reported even if evaluating an earlier part would fail.

The input is read as a sequence of tokens followed by an end-of-input token
whose position is `len(expr)`. When the parser finds a token it cannot use,
the error position is that token's start. For example:

| Formula | Position | Why |
|---|---|---|
| `""` or `"   "` | 0 or 3 | expected an operand, found end of input |
| `1 +` | 3 | expected an operand, found end of input |
| `(1 + 2` | 6 | expected `)`, found end of input |
| `1 + 2)` | 5 | unexpected `)` |
| `2 3` | 2 | two operands in a row |
| `2x` | 1 | two operands in a row |
| `1 * * 2` | 4 | expected an operand, found `*` |
| `min(1,)` | 6 | expected an operand, found `)` |
| `1, 2` | 1 | a comma outside a call |
| `3 $ 4` | 2 | unexpected character |

## Evaluation

Evaluation happens left to right: the left operand of a binary operator is
evaluated before the right one, and call arguments in order. The first error
met in that order is the one raised.

- Names are looked up in `variables` first, then in `CONSTANTS` from
  `calc/functions.py` (`pi`, `e`). An unknown name is an error at the name's
  position.
- Functions come from `FUNCTIONS` in `calc/functions.py` (a variable can't be
  called). An unknown function, or a call with a number of arguments outside
  the function's allowed range, is an error at the function name's position.
  The argument count is checked before the arguments are evaluated.
- An error raised while computing a function (for example `sqrt(-1)`) is an
  error at the function name's position.
- `/` and `%` by zero are errors at the operator's position.
- `%` is floored modulo, like Python's `%`: `-7 % 3` is 2.
- `a ^ b` is an error at the `^` when the result is not a finite real number,
  for example `0 ^ -1`, `(-8) ^ (1/3)` and `10 ^ 400`.
- Values from `variables` may be `int` or `float`; the result is always a
  `float`.
