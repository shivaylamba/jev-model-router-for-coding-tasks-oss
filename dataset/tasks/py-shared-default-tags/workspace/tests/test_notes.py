import unittest

from notes import add_tag, create_note, remove_tag
from search import notes_with_tag


class NotesTest(unittest.TestCase):
    def test_create_with_tags(self):
        note = create_note("  Groceries ", "milk", ["Home", " errands "])
        self.assertEqual(note["title"], "Groceries")
        self.assertEqual(note["tags"], ["home", "errands"])

    def test_add_and_remove_tag(self):
        note = create_note("Plan", tags=["work"])
        add_tag(note, "Urgent")
        self.assertEqual(note["tags"], ["work", "urgent"])
        remove_tag(note, "WORK")
        self.assertEqual(note["tags"], ["urgent"])

    def test_search(self):
        a = create_note("a", tags=["x"])
        b = create_note("b", tags=["y"])
        self.assertEqual(notes_with_tag([a, b], "Y"), [b])


if __name__ == "__main__":
    unittest.main()
