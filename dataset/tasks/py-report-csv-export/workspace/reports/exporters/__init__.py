"""Output formats."""

from .markdown import MarkdownExporter
from .text import TextExporter


class UnknownFormatError(LookupError):
    """Raised by get_exporter for a format name that is not registered."""


EXPORTERS = {exporter.name: exporter for exporter in (TextExporter(), MarkdownExporter())}


def get_exporter(name):
    try:
        return EXPORTERS[name]
    except KeyError:
        raise UnknownFormatError(name) from None


def format_names():
    return sorted(EXPORTERS)
