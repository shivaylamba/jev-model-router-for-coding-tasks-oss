# timesheets

Builds the weekly hours report that finance downloads at month end. Entries are
read from a CSV export (`date,hours`), grouped into ISO weeks and split into
pages for the PDF renderer.

- `timesheets/entries.py`: parse the CSV export.
- `timesheets/weeks.py`: week keys and week boundaries.
- `timesheets/report.py`: weekly totals, pagination, report assembly.
- `timesheets/render.py`: plain-text rendering of a report.

Python 3.11, standard library only. Run the tests with
`python3 -m unittest discover -s tests -t .`
