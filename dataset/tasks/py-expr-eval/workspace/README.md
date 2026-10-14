# calc

The formula engine behind the pricing sheet's computed columns. Users type
formulas such as `base * (1 + rate) ^ years` and we evaluate them against the
row's values. The formula language is specified in `SPEC.md`.

Standard library only (Python 3.11). Run the tests with
`python3 -m unittest discover -s tests -t .`
