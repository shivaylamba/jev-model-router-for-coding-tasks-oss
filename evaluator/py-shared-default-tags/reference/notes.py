"""Notes and tags."""

import itertools

_ids = itertools.count(1)


def normalize_tag(tag):
    """Tags are compared case-insensitively and without surrounding whitespace."""
    return tag.strip().lower()


def create_note(title, body="", tags=None, pinned=False):
    """Create a new note.

    title: the note title; surrounding whitespace is removed.
    body: the note text.
    tags: an optional list or tuple of tag strings. Each tag is normalized with
        normalize_tag.
    pinned: when True, the tag "pinned" is added at the end of the note's tags
        (unless it is already there).

    Returns a dict with keys "id", "title", "body", "tags" (a list) and "pinned".
    Every note gets its own tags list, and the sequence passed in as `tags` is
    never modified.
    """
    note_tags = [normalize_tag(tag) for tag in (tags or ())]
    if pinned and "pinned" not in note_tags:
        note_tags.append("pinned")
    return {
        "id": next(_ids),
        "title": title.strip(),
        "body": body,
        "tags": note_tags,
        "pinned": pinned,
    }


def add_tag(note, tag):
    """Add a tag to a note in place, if the note does not already have it."""
    tag = normalize_tag(tag)
    if tag not in note["tags"]:
        note["tags"].append(tag)
    return note


def remove_tag(note, tag):
    """Remove a tag from a note in place, if present."""
    tag = normalize_tag(tag)
    if tag in note["tags"]:
        note["tags"].remove(tag)
    return note
