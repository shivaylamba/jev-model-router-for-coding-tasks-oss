# minicron

The job runner behind our nightly maintenance tasks. Jobs are registered with a
five-field cron expression and the runner asks when each one should run next.

- `jobs.py` - the job registry and `plan()`, which lists upcoming runs
- `cron.py` - cron expression evaluation (see `SPEC.md` for the exact rules we support)

Standard library only (Python 3.11). All functions take explicit datetimes;
nothing reads the system clock.

Run the tests with `python3 -m unittest discover -s tests -t .`
