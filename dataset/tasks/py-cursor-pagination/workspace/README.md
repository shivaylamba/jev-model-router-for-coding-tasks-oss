# articles

The article listing behind our CMS's public API. Three layers:

- `articles/store.py`: in-memory table (stands in for the database in this repo)
- `articles/repository.py`: queries against the store
- `articles/service.py`: validation and paging rules
- `articles/api.py`: turns query-string parameters into a `(status, body)` response
- `articles/errors.py`: exception types shared by the layers
- `docs/`: design notes

Run the tests with `python3 -m unittest discover -s tests -t .`
