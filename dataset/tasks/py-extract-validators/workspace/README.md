# accounts

Account sign-up and profile editing for the community site.

- `accounts/signup.py`: validates and normalises a new registration.
- `accounts/profile.py`: applies partial updates to an existing profile.
- `accounts/errors.py`: `ValidationError`, which carries the offending field name.

Python 3.11, standard library only. Run the tests with:

    python3 -m unittest discover -s tests -t .
