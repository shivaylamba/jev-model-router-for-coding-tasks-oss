"""Queries against the article store."""


def _order_key(article):
    """Newest first; ties by id, highest first."""
    return (-article.published_at, -article.id)


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
        """Newest first, ties by id descending."""
        rows = sorted(self._filtered(author, status), key=_order_key)
        return rows[offset:offset + limit]

    def list_after(self, after, limit, author=None, status=None):
        """Up to `limit` articles that sort strictly after `after`.

        `after` is a (published_at, id) position or None for the start.
        """
        rows = sorted(self._filtered(author, status), key=_order_key)
        if after is not None:
            position = (-after[0], -after[1])
            rows = [a for a in rows if _order_key(a) > position]
        return rows[:limit]
