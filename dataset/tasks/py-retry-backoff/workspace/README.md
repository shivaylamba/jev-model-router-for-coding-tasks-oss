# feedsync

Pulls JSON feeds from partner endpoints and stores them locally.

- `errors.py` - the exception types the transport raises
- `httpclient.py` - `fetch_json`, which talks to a transport object and retries transient failures

Standard library only (Python 3.11). Every function that waits takes a `sleep`
argument so tests never sleep for real.

Run the tests with `python3 -m unittest discover -s tests -t .`
