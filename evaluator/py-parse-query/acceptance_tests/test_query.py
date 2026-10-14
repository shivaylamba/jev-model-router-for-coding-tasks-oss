import unittest

from urlbits import build_query, parse_query


class ParseQueryTest(unittest.TestCase):
    def test_basic_and_repeated_keys(self):
        result = parse_query("a=1&b=2&a=3")
        self.assertEqual(result, {"a": ["1", "3"], "b": ["2"]})
        self.assertEqual(list(result), ["a", "b"])

    def test_leading_question_mark_and_empty_segments(self):
        self.assertEqual(parse_query("?&a=1&&b=2&"), {"a": ["1"], "b": ["2"]})
        self.assertEqual(parse_query(""), {})
        self.assertEqual(parse_query("?"), {})

    def test_bare_key_and_empty_value(self):
        self.assertEqual(parse_query("flag&x=&flag"), {"flag": [None, None], "x": [""]})

    def test_split_on_first_equals(self):
        self.assertEqual(parse_query("expr=a=b"), {"expr": ["a=b"]})

    def test_plus_and_percent_decoding(self):
        self.assertEqual(parse_query("q=hello+world%21&c%2Bd=1%2B1"), {"q": ["hello world!"], "c+d": ["1+1"]})

    def test_utf8_decoding(self):
        self.assertEqual(parse_query("name=Jos%C3%A9&city=%e6%9d%b1%e4%ba%ac"), {"name": ["José"], "city": ["東京"]})

    def test_malformed_escapes_kept(self):
        self.assertEqual(parse_query("p=100%&q=%zz1&r=%4"), {"p": ["100%"], "q": ["%zz1"], "r": ["%4"]})

    def test_invalid_utf8_replaced(self):
        self.assertEqual(parse_query("b=%FFok"), {"b": ["�ok"]})


class BuildQueryTest(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(build_query({"a": "1", "b": ["2", "3"]}), "a=1&b=2&b=3")

    def test_none_and_empty(self):
        self.assertEqual(build_query({"flag": None, "x": "", "y": [None, "v"]}), "flag&x=&y&y=v")

    def test_empty_list_omits_key(self):
        self.assertEqual(build_query({"a": [], "b": "1"}), "b=1")
        self.assertEqual(build_query({}), "")

    def test_encoding(self):
        self.assertEqual(build_query({"q": "a b&c=d/é~-._"}), "q=a+b%26c%3Dd%2F%C3%A9~-._")
        self.assertEqual(build_query({"k y+": "1+1"}), "k+y%2B=1%2B1")

    def test_type_errors(self):
        with self.assertRaises(TypeError):
            build_query({"n": 5})
        with self.assertRaises(TypeError):
            build_query({"n": ["ok", 5]})


class RoundTripTest(unittest.TestCase):
    def test_parse_then_build(self):
        for query in ["a=1&a=3&b=2", "flag&x=&q=a+b%2B%C3%A9", "k%26=v%3D"]:
            self.assertEqual(build_query(parse_query(query)), query)

    def test_build_then_parse(self):
        params = {"text": ["50% off & more", "x"], "flag": [None], "empty": [""], "uni": ["日本 語+"]}
        self.assertEqual(parse_query(build_query(params)), params)
