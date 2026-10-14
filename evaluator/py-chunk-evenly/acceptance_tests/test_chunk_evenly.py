import unittest

from listutil import chunk_evenly


class ChunkEvenlyTest(unittest.TestCase):
    def test_example(self):
        self.assertEqual(chunk_evenly([1, 2, 3, 4, 5], 3), [[1, 2], [3, 4], [5]])

    def test_even_split(self):
        self.assertEqual(chunk_evenly([1, 2, 3, 4, 5, 6], 3), [[1, 2], [3, 4], [5, 6]])

    def test_longer_chunks_first(self):
        self.assertEqual([len(c) for c in chunk_evenly(list(range(10)), 4)], [3, 3, 2, 2])

    def test_more_chunks_than_items(self):
        self.assertEqual(chunk_evenly([1, 2], 4), [[1], [2], [], []])

    def test_single_chunk(self):
        self.assertEqual(chunk_evenly([1, 2, 3], 1), [[1, 2, 3]])

    def test_empty_input(self):
        self.assertEqual(chunk_evenly([], 2), [[], []])

    def test_invalid_n(self):
        with self.assertRaises(ValueError):
            chunk_evenly([1, 2], 0)
        with self.assertRaises(ValueError):
            chunk_evenly([1, 2], -1)

    def test_input_not_modified(self):
        data = [1, 2, 3]
        chunk_evenly(data, 2)
        self.assertEqual(data, [1, 2, 3])
