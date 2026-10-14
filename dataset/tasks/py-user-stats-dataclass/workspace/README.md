# activity

Per-user activity statistics computed from the product event log, plus the two
things built on them: the admin dashboard rows (`dashboard.py`) and the
re-engagement email job (`emailer.py`).

- `events.py`: the `Event` record
- `stats.py`: `get_user_stats` and `get_all_user_stats`
- `dashboard.py`, `emailer.py`: callers

All timestamps are timezone-aware UTC datetimes.

Run the tests with `python3 -m unittest discover -s tests -t .`
