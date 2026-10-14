"""Listing rules for articles."""

from .errors import ValidationError
from .store import STATUSES

MAX_PER_PAGE = 100


class ArticleService:
    def __init__(self, repository):
        self._repo = repository

    def _check_filters(self, author, status):
        if status is not None and status not in STATUSES:
            raise ValidationError(f"status must be one of {', '.join(STATUSES)}")

    def list_page(self, page=1, per_page=20, author=None, status=None):
        """One page of articles, newest first.

        Returns {"items": [Article, ...], "page": page, "per_page": per_page, "total": total}
        where total counts every article matching the filters.
        """
        if not isinstance(page, int) or page < 1:
            raise ValidationError("page must be an integer >= 1")
        if not isinstance(per_page, int) or not 1 <= per_page <= MAX_PER_PAGE:
            raise ValidationError(f"per_page must be an integer from 1 to {MAX_PER_PAGE}")
        self._check_filters(author, status)
        items = self._repo.list_offset((page - 1) * per_page, per_page, author, status)
        return {"items": items, "page": page, "per_page": per_page, "total": self._repo.count(author, status)}
