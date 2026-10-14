"""Searching notes by tag."""

from notes import normalize_tag


def notes_with_tag(notes, tag):
    """Return the notes that carry `tag`, in their original order."""
    wanted = normalize_tag(tag)
    return [note for note in notes if wanted in note["tags"]]


def tag_counts(notes):
    """Return {tag: number of notes with that tag}."""
    counts = {}
    for note in notes:
        for tag in note["tags"]:
            counts[tag] = counts.get(tag, 0) + 1
    return counts
