# Reservations: intended behaviour

This is the contract the checkout, the support tool and the mobile app rely on.

## Holds

`ReservationService(ledger, clock, hold_ttl=900)` places holds that last
`hold_ttl` seconds: a hold created at time `t` has `expires_at = t + hold_ttl`
and is **expired from the moment `clock.now() >= expires_at`**.

A hold's `status` is one of:

- `"held"`: active, not yet expired;
- `"confirmed"`: paid for; the units have left the ledger;
- `"released"`: given back before it expired;
- `"expired"`: was held and its time ran out without being confirmed or released.

Expiry needs no background job: as soon as the clock passes the expiry time,
the hold is reported as `"expired"` by `get_hold` and by anything that returns
the hold, and its units stop counting against availability.
`sweep_expired()` exists for housekeeping only (it marks expired holds and
returns how many it marked); running it or not must make no observable
difference to availability or to what any other method returns.

## Availability

`available(sku)` is the units on hand in the ledger minus the units in holds
for that SKU that are `"held"` (active and unexpired). Unknown SKUs have 0 on
hand.

## `reserve(sku, quantity, request_id) -> Hold`

- `quantity` must be an `int` of at least 1 and `request_id` a non-empty string;
  otherwise `ValueError`.
- `request_id` makes retries safe. If a hold was already created for this
  `request_id`, the call returns **that same hold** (same `id`), whatever its
  status is now, and changes nothing. If the earlier hold was for a different
  `sku` or `quantity`, it raises `IdempotencyConflictError` instead.
- Otherwise, if `quantity` is more than `available(sku)`, it raises
  `InsufficientStockError` and creates nothing (a later call with the same
  `request_id` is treated as new).
- Otherwise it creates a `"held"` hold.

## `release(hold_id) -> bool`

- `"held"` hold: becomes `"released"`, its units are available again; returns `True`.
- Already `"released"` or `"expired"`: nothing changes; returns `False`.
- `"confirmed"`: raises `HoldStateError` (the goods are sold; returns go
  through a different process).
- Unknown id: `HoldNotFoundError`.

## `confirm(hold_id) -> Hold`

- `"held"` hold: removes its units from the ledger, becomes `"confirmed"`,
  returns the hold.
- Already `"confirmed"`: returns the hold and changes nothing (a double click
  on "Pay" must not take the stock twice).
- `"expired"`: raises `HoldExpiredError`; nothing changes.
- `"released"`: raises `HoldStateError`; nothing changes.
- Unknown id: `HoldNotFoundError`.

## `get_hold(hold_id) -> Hold`

Returns the hold with its current status. Unknown id: `HoldNotFoundError`.
