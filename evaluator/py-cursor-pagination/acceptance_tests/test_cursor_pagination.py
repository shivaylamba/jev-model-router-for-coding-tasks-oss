import base64
import re
import unittest
import warnings

from articles.api import ArticlesApi
from articles.errors import InvalidCursorError, ValidationError
from articles.repository import ArticleRepository
from articles.service import ArticleService, Page
from articles.store import ArticleStore


def build(rows):
    store = ArticleStore()
    for title, author, status, published_at in rows:
        store.insert(title, author, status, published_at)
    service = ArticleService(ArticleRepository(store))
    return store, service, ArticlesApi(service)


# Lots of ties on published_at on purpose.
ROWS = [
    ("a1", "ana", "published", 100),  # 1
    ("a2", "bo", "published", 300),  # 2
    ("a3", "ana", "draft", 300),  # 3
    ("a4", "ana", "published", 300),  # 4
    ("a5", "bo", "archived", 200),  # 5
    ("a6", "ana", "published", 200),  # 6
    ("a7", "cy", "published", 300),  # 7
    ("a8", "ana", "published", 50),  # 8
]
# published_at desc, then id desc
FULL_ORDER = [7, 4, 3, 2, 6, 5, 1, 8]


def ids(items):
    return [a.id for a in items]


def collect(service, limit, **filters):
    seen, cursor, pages = [], None, 0
    while True:
        page = service.list_articles(limit=limit, cursor=cursor, **filters)
        seen.extend(ids(page.items))
        pages += 1
        if page.next_cursor is None:
            return seen, pages
        cursor = page.next_cursor
        if pages > 50:
            raise AssertionError("pagination does not terminate")


class ServiceCursorTest(unittest.TestCase):
    def test_first_page_and_order(self):
        _, service, _ = build(ROWS)
        page = service.list_articles(limit=3)
        self.assertIsInstance(page, Page)
        self.assertEqual(ids(page.items), [7, 4, 3])
        self.assertIsInstance(page.next_cursor, str)

    def test_default_limit_is_20(self):
        _, service, _ = build([(f"t{i}", "ana", "published", i) for i in range(25)])
        page = service.list_articles()
        self.assertEqual(len(page.items), 20)
        self.assertIsNotNone(page.next_cursor)

    def test_walk_all_pages_with_ties(self):
        _, service, _ = build(ROWS)
        for limit in (1, 2, 3, 5, 8, 100):
            seen, _ = collect(service, limit)
            self.assertEqual(seen, FULL_ORDER, f"limit={limit}")

    def test_no_cursor_when_exactly_exhausted(self):
        _, service, _ = build(ROWS)
        first = service.list_articles(limit=4)
        second = service.list_articles(limit=4, cursor=first.next_cursor)
        self.assertEqual(ids(second.items), [6, 5, 1, 8])
        self.assertIsNone(second.next_cursor)
        self.assertIsNone(service.list_articles(limit=8).next_cursor)

    def test_empty_result(self):
        _, service, _ = build(ROWS)
        page = service.list_articles(author="nobody")
        self.assertEqual(page.items, [])
        self.assertIsNone(page.next_cursor)

    def test_filters(self):
        _, service, _ = build(ROWS)
        self.assertEqual(collect(service, 2, author="ana")[0], [4, 3, 6, 1, 8])
        self.assertEqual(collect(service, 2, status="published")[0], [7, 4, 2, 6, 1, 8])
        self.assertEqual(collect(service, 1, author="ana", status="published")[0], [4, 6, 1, 8])

    def test_limit_may_change_between_pages(self):
        _, service, _ = build(ROWS)
        first = service.list_articles(limit=2)
        second = service.list_articles(limit=5, cursor=first.next_cursor)
        self.assertEqual(ids(second.items), [3, 2, 6, 5, 1])

    def test_cursor_is_url_safe(self):
        _, service, _ = build(ROWS)
        cursor = service.list_articles(limit=2, author="ana", status="published").next_cursor
        self.assertRegex(cursor, r"^[A-Za-z0-9_-]+$")

    def test_inserts_during_paging(self):
        store, service, _ = build(ROWS)
        first = service.list_articles(limit=3)  # 7, 4, 3; cursor at (300, 3)
        store.insert("newest", "ana", "published", 999)  # 9: before the cursor
        store.insert("same time, higher id", "ana", "published", 300)  # 10: before the cursor
        store.insert("oldest", "ana", "published", 1)  # 11: after the cursor
        rest, cursor = [], first.next_cursor
        while cursor is not None:
            page = service.list_articles(limit=3, cursor=cursor)
            rest.extend(ids(page.items))
            cursor = page.next_cursor
        self.assertEqual(rest, [2, 6, 5, 1, 8, 11])

    def test_deleting_the_cursor_article(self):
        store, service, _ = build(ROWS)
        first = service.list_articles(limit=2)  # 7, 4
        store.delete(4)
        second = service.list_articles(limit=2, cursor=first.next_cursor)
        self.assertEqual(ids(second.items), [3, 2])

    def test_cursor_with_other_filters_is_rejected(self):
        _, service, _ = build(ROWS)
        cursor = service.list_articles(limit=1, author="ana").next_cursor
        with self.assertRaises(InvalidCursorError):
            service.list_articles(limit=1, cursor=cursor)
        with self.assertRaises(InvalidCursorError):
            service.list_articles(limit=1, cursor=cursor, author="bo")
        with self.assertRaises(InvalidCursorError):
            service.list_articles(limit=1, cursor=cursor, author="ana", status="draft")

    def test_garbage_cursors(self):
        _, service, _ = build(ROWS)
        self.assertTrue(issubclass(InvalidCursorError, ValidationError))
        junk = [
            "",
            "not a cursor",
            "!!!",
            "AAAA",
            base64.urlsafe_b64encode(b'{"x": 1}').decode().rstrip("="),
            base64.urlsafe_b64encode(b"[1, 2, 3]").decode().rstrip("="),
            base64.urlsafe_b64encode(b"\xff\xfe\x00").decode().rstrip("="),
        ]
        for value in junk:
            with self.assertRaises(InvalidCursorError, msg=repr(value)):
                service.list_articles(cursor=value)

    def test_limit_and_status_validation(self):
        _, service, _ = build(ROWS)
        for bad in (0, 101, -1, "10", 2.0, True):
            with self.assertRaises(ValidationError, msg=repr(bad)):
                service.list_articles(limit=bad)
        self.assertEqual(len(service.list_articles(limit=100).items), 8)
        with self.assertRaises(ValidationError):
            service.list_articles(status="deleted")


class LegacyWrapperTest(unittest.TestCase):
    def test_list_page_warns_and_still_works(self):
        _, service, _ = build(ROWS)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = service.list_page(page=2, per_page=3)
            service.list_page()
        deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        self.assertEqual(len(deprecations), 2)
        self.assertEqual(ids(result["items"]), [2, 6, 5])
        self.assertEqual((result["page"], result["per_page"], result["total"]), (2, 3, 8))

    def test_list_page_validation_unchanged(self):
        _, service, _ = build(ROWS)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            with self.assertRaises(ValidationError):
                service.list_page(page=0)
            with self.assertRaises(ValidationError):
                service.list_page(per_page=101)


class ApiTest(unittest.TestCase):
    def setUp(self):
        _, _, self.api = build(ROWS)

    def test_cursor_mode_default(self):
        status, body = self.api.handle_list({})
        self.assertEqual(status, 200)
        self.assertEqual(set(body), {"items", "next_cursor"})
        self.assertEqual([a["id"] for a in body["items"]], FULL_ORDER)
        self.assertIsNone(body["next_cursor"])
        self.assertEqual(body["items"][0], {"id": 7, "title": "a7", "author": "cy", "status": "published", "published_at": 300})

    def test_cursor_mode_paging_with_filters(self):
        status, body = self.api.handle_list({"limit": "2", "author": "ana"})
        self.assertEqual(status, 200)
        self.assertEqual([a["id"] for a in body["items"]], [4, 3])
        status, body = self.api.handle_list({"limit": "2", "author": "ana", "cursor": body["next_cursor"]})
        self.assertEqual([a["id"] for a in body["items"]], [6, 1])
        status, body = self.api.handle_list({"limit": "2", "author": "ana", "cursor": body["next_cursor"]})
        self.assertEqual([a["id"] for a in body["items"]], [8])
        self.assertIsNone(body["next_cursor"])

    def test_empty_cursor_param_means_first_page(self):
        status, body = self.api.handle_list({"limit": "1", "cursor": ""})
        self.assertEqual(status, 200)
        self.assertEqual([a["id"] for a in body["items"]], [7])

    def test_errors_are_400(self):
        _, first = self.api.handle_list({"limit": "1", "author": "ana"})
        for params in (
            {"cursor": "garbage"},
            {"cursor": first["next_cursor"]},
            {"limit": "abc"},
            {"limit": "0"},
            {"limit": "500"},
            {"status": "deleted"},
            {"page": "1", "cursor": first["next_cursor"]},
            {"per_page": "5", "limit": "5"},
        ):
            status, body = self.api.handle_list(params)
            self.assertEqual(status, 400, params)
            self.assertIsInstance(body.get("error"), str, params)

    def test_legacy_mode(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            status, body = self.api.handle_list({"page": "2", "per_page": "3"})
        self.assertEqual(status, 200)
        self.assertEqual(set(body), {"items", "page", "per_page", "total"})
        self.assertEqual([a["id"] for a in body["items"]], [2, 6, 5])
        self.assertEqual(body["total"], 8)
