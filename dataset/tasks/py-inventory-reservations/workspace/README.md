# inventory

Stock reservations for the shop checkout. When a shopper starts checkout we
place a *hold* on the stock for a limited time; paying confirms the hold
(stock leaves the warehouse), abandoning the cart releases it, and an
unattended hold expires on its own.

- `inventory/stock.py`: `StockLedger`, units physically on hand per SKU
- `inventory/holds.py`: the `Hold` record and its in-memory store
- `inventory/service.py`: `ReservationService`, the API checkout calls
- `inventory/clock.py`: clocks (`SystemClock`, and `ManualClock` for tests)
- `inventory/errors.py`: exception types
- `docs/reservations.md`: how reservations are meant to behave

Run the tests with `python3 -m unittest discover -s tests -t .`
