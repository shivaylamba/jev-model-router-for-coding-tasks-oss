"""Queries against the article store."""


class ArticleRepository:
    def __init__(self, store):
        self._store = store

    def _filtered(self, author=None, status=None):
        rows = self._store.scan()
        if author is not None:
            rows = [a for a in rows if a.author == author]
        if status is not None:
            rows = [a for a in rows if a.status == status]
        return rows

    def count(self, author=None, status=None):
        return len(self._filtered(author, status))

    def list_offset(self, offset, limit, author=None, status=None):
        """Newest first."""
        rows = sorted(self._filtered(author, status), key=lambda a: a.published_at, reverse=True)
        return rows[offset:offset + limit]
