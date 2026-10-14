import unittest

from notes import add_tag, create_note
from search import tag_counts


class NoteTagsTest(unittest.TestCase):
    def test_pinned_tag_does_not_leak(self):
        create_note("Standup", pinned=True)
        plain = create_note("Groceries")
        self.assertEqual(plain["tags"], [])

    def test_untagged_notes_do_not_share_tags(self):
        a = create_note("a")
        b = create_note("b")
        add_tag(a, "work")
        self.assertEqual(a["tags"], ["work"])
        self.assertEqual(b["tags"], [])
        self.assertEqual(create_note("c")["tags"], [])

    def test_tag_counts(self):
        a = create_note("a")
        b = create_note("b")
        add_tag(a, "work")
        self.assertEqual(tag_counts([a, b]), {"work": 1})

    def test_caller_list_is_not_modified(self):
        shared = ["Inbox", " Work "]
        first = create_note("one", tags=shared, pinned=True)
        second = create_note("two", tags=shared)
        self.assertEqual(shared, ["Inbox", " Work "])
        self.assertEqual(first["tags"], ["inbox", "work", "pinned"])
        self.assertEqual(second["tags"], ["inbox", "work"])

    def test_notes_with_same_input_list_are_independent(self):
        shared = ["x"]
        first = create_note("one", tags=shared)
        second = create_note("two", tags=shared)
        add_tag(first, "y")
        self.assertEqual(second["tags"], ["x"])
        self.assertIsNot(first["tags"], shared)

    def test_tuple_tags(self):
        note = create_note("t", tags=("A", "b"), pinned=True)
        self.assertEqual(note["tags"], ["a", "b", "pinned"])

    def test_pinned_not_duplicated(self):
        note = create_note("p", tags=["Pinned"], pinned=True)
        self.assertEqual(note["tags"], ["pinned"])
        self.assertTrue(note["pinned"])


if __name__ == "__main__":
    unittest.main()
