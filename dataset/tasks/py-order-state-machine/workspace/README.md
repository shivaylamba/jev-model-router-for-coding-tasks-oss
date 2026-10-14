# shop

Order handling for the shop back office.

- `shop/orders.py`: the `Order` object and its lifecycle methods.
- `shop/reports.py`: status summaries for the dashboard.
- `docs/ORDER_LIFECYCLE.md`: which status changes are allowed.

Python 3.11, standard library only. Run the tests with:

    python3 -m unittest discover -s tests -t .
