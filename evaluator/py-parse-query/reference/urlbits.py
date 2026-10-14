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


_UNRESERVED = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")
_HEX = "0123456789abcdefABCDEF"


def _decode(text):
    text = text.replace("+", " ")
    out = bytearray()
    i = 0
    while i < len(text):
        ch = text[i]
        pair = text[i + 1:i + 3]
        if ch == "%" and len(pair) == 2 and all(c in _HEX for c in pair):
            out.append(int(pair, 16))
            i += 3
        else:
            out.extend(ch.encode("utf-8"))
            i += 1
    return out.decode("utf-8", errors="replace")


def _encode(text):
    parts = []
    for byte in text.encode("utf-8"):
        if byte in _UNRESERVED:
            parts.append(chr(byte))
        elif byte == 0x20:
            parts.append("+")
        else:
            parts.append(f"%{byte:02X}")
    return "".join(parts)


def parse_query(query):
    """Parse a query string into {key: [value, ...]} (see build_query)."""
    if query.startswith("?"):
        query = query[1:]
    result = {}
    for segment in query.split("&"):
        if segment == "":
            continue
        if "=" in segment:
            raw_key, raw_value = segment.split("=", 1)
            value = _decode(raw_value)
        else:
            raw_key, value = segment, None
        result.setdefault(_decode(raw_key), []).append(value)
    return result


def build_query(params):
    """Build a query string (without "?") from {key: value or [values]}."""
    parts = []
    for key, value in params.items():
        if not isinstance(key, str):
            raise TypeError(f"query keys must be str, got {type(key).__name__}")
        values = value if isinstance(value, list) else [value]
        for item in values:
            if item is None:
                parts.append(_encode(key))
            elif isinstance(item, str):
                parts.append(f"{_encode(key)}={_encode(item)}")
            else:
                raise TypeError(f"query values must be str or None, got {type(item).__name__}")
    return "&".join(parts)
