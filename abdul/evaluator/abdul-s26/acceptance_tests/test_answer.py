import json, math, unittest
from pathlib import Path

# Abdul's equality rule, copied from amrrs/jev-router-experiment grade.py at 56b4c3b.
def equal(a, b):
    if isinstance(b, bool) or b is None: return a is b
    if isinstance(b, (float, int)): return type(a) in (int, float) and math.isclose(a, b, rel_tol=0, abs_tol=1e-4)
    if isinstance(b, list): return isinstance(a, list) and len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    if isinstance(b, dict): return isinstance(a, dict) and a.keys() == b.keys() and all(equal(a[k], v) for k, v in b.items())
    return a == b

EXPECTED = json.loads('{"urgent": false}')

class T(unittest.TestCase):
    def test_answer(self):
        text = Path("answer.json").read_text()
        self.assertTrue(equal(json.loads(text), EXPECTED), f"got {text!r}")

if __name__ == "__main__":
    unittest.main()
