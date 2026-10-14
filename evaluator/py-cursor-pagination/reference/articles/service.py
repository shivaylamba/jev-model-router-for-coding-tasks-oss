"""Listing rules for articles."""

import base64
import binascii
import json
import warnings
from dataclasses import dataclass, field

from .errors import InvalidCursorError, ValidationError
from .store import STATUSES

MAX_PER_PAGE = 100
_CURSOR_VERSION = 1


@dataclass
class Page:
    items: list = field(default_factory=list)
    next_cursor: str | None = None


def _encode_cursor(article, author, status):
    payload = {"v": _CURSOR_VERSION, "p": article.published_at, "i": article.id, "a": author, "s": status}
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _decode_cursor(cursor):
    if not isinstance(cursor, str) or not cursor:
        raise InvalidCursorError("invalid cursor")
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
        payload = json.loads(raw.decode())
    except (binascii.Error, ValueError, UnicodeDecodeError):
        raise InvalidCursorError("invalid cursor") from None
    if not isinstance(payload, dict) or set(payload) != {"v", "p", "i", "a", "s"} or payload["v"] != _CURSOR_VERSION:
        raise InvalidCursorError("invalid cursor")
    p, i, a, s = payload["p"], payload["i"], payload["a"], payload["s"]
    for number in (p, i):
        if not isinstance(number, int) or isinstance(number, bool):
            raise InvalidCursorError("invalid cursor")
    if not (a is None or isinstance(a, str)) or not (s is None or isinstance(s, str)):
        raise InvalidCursorError("invalid cursor")
    return (p, i), a, s


class ArticleService:
    def __init__(self, repository):
        self._repo = repository

    def _check_filters(self, author, status):
        if status is not None and status not in STATUSES:
            raise ValidationError(f"status must be one of {', '.join(STATUSES)}")

    def list_articles(self, limit=20, cursor=None, author=None, status=None):
        """A page of articles, newest first; see docs/pagination.md."""
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_PER_PAGE:
            raise ValidationError(f"limit must be an integer from 1 to {MAX_PER_PAGE}")
        self._check_filters(author, status)
        after = None
        if cursor is not None:
            after, cursor_author, cursor_status = _decode_cursor(cursor)
            if cursor_author != author or cursor_status != status:
                raise InvalidCursorError("cursor was created with different filters")
        rows = self._repo.list_after(after, limit + 1, author, status)
        items = rows[:limit]
        next_cursor = _encode_cursor(items[-1], author, status) if len(rows) > limit else None
        return Page(items=items, next_cursor=next_cursor)

    def list_page(self, page=1, per_page=20, author=None, status=None):
        """Deprecated: use list_articles.

        Returns {"items": [Article, ...], "page": page, "per_page": per_page, "total": total}
        where total counts every article matching the filters.
        """
        warnings.warn("list_page is deprecated; use list_articles", DeprecationWarning, stacklevel=2)
        if not isinstance(page, int) or page < 1:
            raise ValidationError("page must be an integer >= 1")
        if not isinstance(per_page, int) or not 1 <= per_page <= MAX_PER_PAGE:
            raise ValidationError(f"per_page must be an integer from 1 to {MAX_PER_PAGE}")
        self._check_filters(author, status)
        items = self._repo.list_offset((page - 1) * per_page, per_page, author, status)
        return {"items": items, "page": page, "per_page": per_page, "total": self._repo.count(author, status)}
