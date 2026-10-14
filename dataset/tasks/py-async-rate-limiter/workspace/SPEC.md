# RateLimiter

`ratelimit.RateLimiter` limits outbound calls per key (one key per customer
endpoint) with a token bucket, and caps the number of calls in flight across
all keys.

```python
limiter = RateLimiter(rate=2.0, burst=5, max_concurrent=10, clock=clock, sleep=sleep)

async with limiter.limit("endpoint-42"):
    await post_webhook(...)
```

## Construction

`RateLimiter(rate, burst, max_concurrent, *, clock, sleep)`

- `rate`: tokens added per second to each key's bucket, a number > 0.
- `burst`: bucket capacity, an int >= 1.
- `max_concurrent`: the most slots that may be held at once across all keys,
  an int >= 1.
- `clock`: a function returning the current time in seconds (float).
- `sleep`: an async function `sleep(seconds)` used for every wait on time.

Invalid `rate`, `burst` or `max_concurrent` raise `ValueError`.

The limiter never reads real time and never waits on time any other way
(no `asyncio.sleep` with a delay, no timeouts, no loop time).

## Buckets

Each key has its own bucket, created full (`burst` tokens) the first time
the key is used. A bucket gains `rate` tokens per second of `clock()` time,
continuously, and never holds more than `burst`. `TokenBucket` in
`ratelimit/bucket.py` already implements this and may be reused or extended.

## Requests and grants

Each `acquire(key)` call is a request. A request is **granted** when it takes
one token from its key's bucket and one concurrency slot, both at once. A
granted request holds its slot until `release()` is called.

1. **FIFO per key.** Requests for the same key are granted in the order
   `acquire` was called. Only the oldest ungranted request of a key (the
   key's *head*) can be granted.
2. **Eligibility.** A head is eligible when its bucket has at least one token
   at the current `clock()` time and fewer than `max_concurrent` slots are
   held.
3. **Grant pass.** Whenever something happens that could make a head
   eligible (an `acquire` call, a `release`, a cancellation, a waiter's sleep
   ending), the limiter grants the eligible head whose `acquire` call came
   first, then looks again, and repeats until no head is eligible. So when a
   slot frees up it goes to the earliest caller among keys that have a token;
   a key that is out of tokens never holds up other keys.
4. **No waiting when not needed.** If a request is granted by the grant pass
   of its own `acquire` call, `acquire` returns without calling `sleep`.
5. **Waiting for a token.** While a head is waiting for a token, the limiter
   calls `sleep(d)` where `d` is exactly the time until the bucket reaches one
   token, computed from `clock()` at that moment (for example 0.5 for an
   empty bucket with `rate=2`). It does not poll with shorter sleeps. When
   that sleep returns it runs a grant pass; if the clock has not advanced far
   enough it sleeps again for the remaining time. A request that becomes the
   head while its key is out of tokens starts this wait right away.
6. **Waiting for a slot.** Requests that only lack a slot do not sleep; they
   are granted by the grant pass of a later `release` or cancellation.
7. **Prompt return.** Once a request is granted, its `acquire` returns as
   soon as its task next runs, without waiting on any pending sleep.

## release()

`release()` frees one slot and runs a grant pass before returning, so if a
request is eligible it is granted inside `release()` and `in_use` does not
drop. Calling `release()` when no slot is held raises `RuntimeError`.

## Cancellation

If the task awaiting `acquire` is cancelled, `CancelledError` propagates
out of `acquire` and the request leaves no trace:

- If it had not been granted, it is removed from its key's queue and
  consumed nothing. If it was the head, the next request for that key becomes
  the head (and starts waiting for a token if needed).
- If it had already been granted but `acquire` had not returned yet (granted
  by a grant pass, then cancelled before its task resumed), the grant is
  undone: the slot is freed and the token goes back into the bucket (still
  capped at `burst`).

Either way a grant pass then runs.

## limit(key)

`limit(key)` returns an async context manager that acquires on entry and
releases on exit, also when the body raises.

## Introspection

- `in_use` (property): the number of slots currently held.
- `tokens(key)`: the key's current token count as a float at `clock()` time
  (`burst` for a key never used).
- `waiting(key=None)`: the number of ungranted requests for `key`, or across
  all keys when `key` is None.
