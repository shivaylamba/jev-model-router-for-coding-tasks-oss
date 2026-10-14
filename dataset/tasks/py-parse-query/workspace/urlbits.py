"""URL helpers for the link checker."""


def split_url(url):
    """Split a URL into (base, query, fragment).

    The query is the text after the first "?" (without the "?") and the
    fragment is the text after the first "#". Missing parts are "".

    >>> split_url("https://x.test/a?b=1#top")
    ('https://x.test/a', 'b=1', 'top')
    """
    base, _, fragment = url.partition("#")
    base, _, query = base.partition("?")
    return base, query, fragment
