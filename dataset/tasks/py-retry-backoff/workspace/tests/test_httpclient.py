import unittest

from errors import PermanentError
from httpclient import fetch_json


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url):
        self.calls.append(url)
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class FetchJsonTest(unittest.TestCase):
    def test_success(self):
        transport = FakeTransport(['{"ok": true}'])
        self.assertEqual(fetch_json(transport, "https://x/feed", sleep=lambda s: None), {"ok": True})
        self.assertEqual(transport.calls, ["https://x/feed"])

    def test_permanent_error_is_not_retried(self):
        transport = FakeTransport([PermanentError("404")])
        with self.assertRaises(PermanentError):
            fetch_json(transport, "https://x/feed", sleep=lambda s: None)
        self.assertEqual(len(transport.calls), 1)


if __name__ == "__main__":
    unittest.main()
