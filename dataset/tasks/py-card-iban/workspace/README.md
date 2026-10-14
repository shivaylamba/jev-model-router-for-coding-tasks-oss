# payment_checks

Input checks used by the checkout service before payment details are sent to
the processor. Everything here is offline: no network lookups, standard library
only (Python 3.11).

- `payment_checks.py`: card and bank-account helpers.
- `iban_countries.py`: IBAN lengths per country.

Run the tests with `python3 -m unittest discover -s tests -t .`
