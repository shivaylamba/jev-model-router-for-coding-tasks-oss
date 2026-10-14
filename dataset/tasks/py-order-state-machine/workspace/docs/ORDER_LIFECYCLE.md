# Order lifecycle

An order starts as `pending`. Each lifecycle method on `Order` is an event that
moves it to a new status. These are the only allowed transitions:

| method                    | from                          | to          |
|---------------------------|-------------------------------|-------------|
| `pay()`                   | `pending`                     | `paid`      |
| `pack()`                  | `paid`                        | `packed`    |
| `ship(tracking_number)`   | `packed`                      | `shipped`   |
| `deliver()`               | `shipped`                     | `delivered` |
| `cancel(reason)`          | `pending`, `paid`, `packed`   | `cancelled` |
| `refund()`                | `paid`, `packed`, `delivered` | `refunded`  |

The event names are the method names: `pay`, `pack`, `ship`, `deliver`,
`cancel`, `refund`.

Rules:

- `cancelled` and `refunded` are terminal: no event is allowed from them.
- A shipped order cannot be cancelled or refunded until it is delivered.
- A delivered order can be refunded only within 30 days of delivery: the
  refund is allowed when `now - delivered_at <= 30 days` (exactly 30 days is
  still allowed), where `delivered_at` is when `deliver()` happened.
- `ship()` needs a tracking number and `cancel()` needs a reason: a value that
  is not a string, or is empty or only whitespace, is rejected. The tracking
  number and reason are stored stripped of surrounding whitespace.
