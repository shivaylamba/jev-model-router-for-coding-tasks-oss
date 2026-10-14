# reports

Turns tabular report data (JSON) into human-readable output.

```
python3 -m reports.cli examples/sales.json                 # plain text table
python3 -m reports.cli --format markdown examples/sales.json
python3 -m reports.cli --format markdown --output out.md examples/sales.json
python3 -m reports.cli --list-formats
```

Input JSON: `{"title": str, "columns": [{"key": str, "label": str}, ...], "rows": [{key: value, ...}, ...]}`.
Cell values are strings, ints, floats, booleans or null; a key missing from a row counts as null.

Layout:

- `reports/model.py`: `Report`, `Column`, `load_report`
- `reports/formatting.py`: display formatting for cells (thousands separators etc.)
- `reports/exporters/`: one module per output format. Each exporter is a class
  with `name`, `extension` and `export(report) -> str`, registered in
  `reports/exporters/__init__.py`; `get_exporter(name)` looks one up and raises
  `UnknownFormatError` for names that are not registered.
- `reports/cli.py`: the command line; `main(argv, stdout)` returns the exit code.

Run the tests with `python3 -m unittest discover -s tests -t .`
