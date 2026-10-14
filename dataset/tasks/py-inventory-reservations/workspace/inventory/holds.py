"""Hold records."""

from dataclasses import dataclass


@dataclass
class Hold:
    id: str
    sku: str
    quantity: int
    request_id: str
    created_at: float
    expires_at: float
    status: str = "held"

    def is_expired(self, now):
        return now > self.expires_at


class HoldStore:
    def __init__(self):
        self._by_id = {}
        self._by_request = {}
        self._next = 1

    def create(self, sku, quantity, request_id, created_at, expires_at):
        hold = Hold(f"h{self._next}", sku, quantity, request_id, created_at, expires_at)
        self._next += 1
        self._by_id[hold.id] = hold
        self._by_request[hold.id] = hold
        return hold

    def get(self, hold_id):
        return self._by_id.get(hold_id)

    def by_request(self, request_id):
        return self._by_request.get(request_id)

    def all(self):
        return list(self._by_id.values())
