"""Text statistics."""
import re
from collections import Counter


def word_counts(text):
    return dict(Counter(w.lower() for w in re.findall(r"[A-Za-z0-9']+", text)))
