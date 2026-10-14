"""In-memory article table."""

from dataclasses import dataclass

STATUSES = ("draft", "published", "archived")


@dataclass(frozen=True)
class Article:
    id: int
    title: str
    author: str
    status: str
    published_at: int  # unix seconds


class ArticleStore:
    def __init__(self):
        self._rows = {}
        self._next_id = 1

    def insert(self, title, author, status, published_at):
        """Add an article; ids are assigned in increasing order starting at 1."""
        if status not in STATUSES:
            raise ValueError(f"unknown status {status!r}")
        article = Article(self._next_id, title, author, status, published_at)
        self._rows[article.id] = article
        self._next_id += 1
        return article

    def delete(self, article_id):
        self._rows.pop(article_id, None)

    def scan(self):
        """Every article, in insertion order."""
        return list(self._rows.values())
