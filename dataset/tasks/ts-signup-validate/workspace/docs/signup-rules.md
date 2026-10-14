# Sign-up validation rules

`validateSignup(input, today)` checks a sign-up request.

- `input` is the parsed request body. Any field may be missing or of the wrong
  type.
- `today` is the current date, passed in by the caller. Only its UTC calendar
  date matters (`getUTCFullYear()`, `getUTCMonth()`, `getUTCDate()`).

## Result

- When every field is valid: `{ ok: true, value: { username, email, birthDate } }`
  with the normalized values described below.
- Otherwise: `{ ok: false, errors }`, where `errors` maps each invalid field name
  to exactly one error code. Fields without an error are not present in
  `errors`.

## General rules

- Each field reports at most one error: the first rule in its list below that
  fails.
- `username`, `email` and `birthDate` are trimmed (leading and trailing
  whitespace removed) before any check. `password` and `confirmPassword` are
  never trimmed.
- `required`: the field is missing, is not a string, or is an empty string
  (after trimming, for trimmed fields).

## username

1. `required`
2. `length`: between 3 and 20 characters inclusive.
3. `format`: only ASCII letters, digits and `_`, and the first character is a
   letter.

Normalized value: trimmed and lowercased.

## email

1. `required`
2. `format`: contains no whitespace and exactly one `@`; the part before `@` is
   not empty; the part after `@` (the domain) is made of at least two
   non-empty labels separated by `.` (so it contains a `.`, does not start or
   end with `.`, and has no `..`).

Normalized value: trimmed and lowercased.

## password

1. `required`
2. `length`: between 8 and 64 characters inclusive.
3. `weak`: contains at least one ASCII letter and at least one ASCII digit.
4. `contains_username`: does not contain the username, compared
   case-insensitively. This rule only applies when the username itself is
   valid.

## confirmPassword

1. `required`
2. `mismatch`: exactly equal to `password`. Skipped when `password` is missing
   or not a string; applied even when `password` has its own error.

## birthDate

1. `required`
2. `format`: `YYYY-MM-DD` with a four-digit year, two-digit month and two-digit
   day forming a real calendar date (February 29 only in leap years), and a
   year of 1900 or later.
3. `future`: not after `today`.
4. `too_young`: the person is at least 13 years old on `today`. A person gains a
   year of age on the anniversary of their birth date; someone born on
   February 29 gains it on March 1 in years that are not leap years.

Normalized value: the trimmed string.
