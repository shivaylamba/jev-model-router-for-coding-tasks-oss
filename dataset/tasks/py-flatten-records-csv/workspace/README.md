# eventdump

Exports audit events from our API (JSON documents) for people who want to open
them in a spreadsheet.

- `loader.py` - reads newline-delimited JSON files into a list of dicts
- `csvexport.py` - CSV output

Standard library only (Python 3.11). Run the tests with
`python3 -m unittest discover -s tests -t .`
