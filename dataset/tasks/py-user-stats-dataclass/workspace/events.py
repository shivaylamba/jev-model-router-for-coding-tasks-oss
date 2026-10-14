"""Product events."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Event:
    user_id: str
    kind: str
    at: datetime
