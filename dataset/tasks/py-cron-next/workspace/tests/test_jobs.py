import unittest

from jobs import Registry


class RegistryTest(unittest.TestCase):
    def test_add_and_list(self):
        reg = Registry()
        reg.add("vacuum", "0 3 * * *")
        reg.add("rotate-logs", "@daily")
        self.assertEqual([j.name for j in reg.jobs()], ["vacuum", "rotate-logs"])

    def test_invalid_names(self):
        reg = Registry()
        for name in ["", "Vacuum", "9lives", "a b"]:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    reg.add(name, "* * * * *")

    def test_duplicate(self):
        reg = Registry()
        reg.add("vacuum", "0 3 * * *")
        with self.assertRaises(ValueError):
            reg.add("vacuum", "0 4 * * *")


if __name__ == "__main__":
    unittest.main()
