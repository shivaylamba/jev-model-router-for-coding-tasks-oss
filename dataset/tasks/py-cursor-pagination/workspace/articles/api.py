"""GET /articles."""

from .errors import ValidationError


def serialize(article):
    return {
        "id": article.id,
        "title": article.title,
        "author": article.author,
        "status": article.status,
        "published_at": article.published_at,
    }


def _int_param(params, name, default):
    raw = params.get(name)
    if raw is None:
        return default
    if not raw.isdigit():
        raise ValidationError(f"{name} must be a positive integer")
    return int(raw)


class ArticlesApi:
    def __init__(self, service):
        self._service = service

    def handle_list(self, params):
        """`params` maps query-string names to string values. Returns (status, body)."""
        try:
            result = self._service.list_page(
                page=_int_param(params, "page", 1),
                per_page=_int_param(params, "per_page", 20),
                author=params.get("author"),
                status=params.get("status"),
            )
        except ValidationError as err:
            return 400, {"error": str(err)}
        body = dict(result)
        body["items"] = [serialize(a) for a in result["items"]]
        return 200, body
