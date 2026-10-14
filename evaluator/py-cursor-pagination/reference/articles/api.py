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
        legacy = "page" in params or "per_page" in params
        try:
            if legacy:
                if "cursor" in params or "limit" in params:
                    raise ValidationError("page/per_page cannot be combined with cursor/limit")
                return 200, self._legacy(params)
            page = self._service.list_articles(
                limit=_int_param(params, "limit", 20),
                cursor=params.get("cursor") or None,
                author=params.get("author"),
                status=params.get("status"),
            )
        except ValidationError as err:
            return 400, {"error": str(err)}
        return 200, {"items": [serialize(a) for a in page.items], "next_cursor": page.next_cursor}

    def _legacy(self, params):
        result = self._service.list_page(
            page=_int_param(params, "page", 1),
            per_page=_int_param(params, "per_page", 20),
            author=params.get("author"),
            status=params.get("status"),
        )
        body = dict(result)
        body["items"] = [serialize(a) for a in result["items"]]
        return body
