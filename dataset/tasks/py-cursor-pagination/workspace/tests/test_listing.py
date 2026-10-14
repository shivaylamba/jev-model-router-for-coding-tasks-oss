import unittest
import warnings

from articles.api import ArticlesApi
from articles.errors import ValidationError
from articles.repository import ArticleRepository
from articles.service import ArticleService
from articles.store import ArticleStore


def build():
    store = ArticleStore()
    store.insert("Hello", "ana", "published", 1000)
    store.insert("Draft notes", "ana", "draft", 2000)
    store.insert("Release 2", "bo", "published", 3000)
    store.insert("Old news", "bo", "archived", 500)
    service = ArticleService(ArticleRepository(store))
    return store, service, ArticlesApi(service)


class OffsetListingTest(unittest.TestCase):
    def setUp(self):
        warnings.simplefilter("ignore", DeprecationWarning)
        self.addCleanup(warnings.resetwarnings)

    def test_first_page(self):
        _, service, _ = build()
        result = service.list_page(page=1, per_page=2)
        self.assertEqual([a.title for a in result["items"]], ["Release 2", "Draft notes"])
        self.assertEqual(result["total"], 4)

    def test_second_page_with_filter(self):
        _, service, _ = build()
        result = service.list_page(page=2, per_page=1, author="bo")
        self.assertEqual([a.title for a in result["items"]], ["Old news"])
        self.assertEqual(result["total"], 2)

    def test_validation(self):
        _, service, _ = build()
        with self.assertRaises(ValidationError):
            service.list_page(page=0)
        with self.assertRaises(ValidationError):
            service.list_page(per_page=101)
        with self.assertRaises(ValidationError):
            service.list_page(status="deleted")

    def test_api_page_params(self):
        _, _, api = build()
        status, body = api.handle_list({"page": "1", "per_page": "3", "status": "published"})
        self.assertEqual(status, 200)
        self.assertEqual([a["id"] for a in body["items"]], [3, 1])
        self.assertEqual((body["page"], body["per_page"], body["total"]), (1, 3, 2))

    def test_api_bad_param(self):
        _, _, api = build()
        status, body = api.handle_list({"page": "two"})
        self.assertEqual(status, 400)
        self.assertIn("error", body)


if __name__ == "__main__":
    unittest.main()
