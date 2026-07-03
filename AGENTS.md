# AI coding agent instructions for `trcks-example-fastapi`

## Project requirements

- `trcks-example-fastapi` is an example FastAPI application that follows
  FastAPI best practices.
- `trcks-example-fastapi` demonstrates type-safe railway-oriented
  programming (ROP) with `trcks` and returns domain errors instead of
  raising them.

## Architecture decisions

### Layers

- Routers (`app/logic/routers/`) define HTTP endpoints.
- Schemas (`app/data_structures/schemas/`) model the HTTP interface.
- Services (`app/logic/services/`) orchestrate business logic.
- Repositories (`app/logic/repositories/`) encapsulate data access.
- Domain objects (`app/data_structures/domain/`) are immutable domain
  models.
- ORM models live in `app/data_structures/models.py`.
- A layer may import only itself or lower layers. Import-linter contracts
  in `pyproject.toml` enforce this order.

### Core patterns

- Use `trcks.Result` and `trcks.AwaitableResult` for explicit success or
  failure return types.
- Routers pattern-match on `Result` values, mapping `Failure` errors to
  `HTTPException`s and returning `Success` payloads with an appropriate
  HTTP status code.
- ORM models provide `to_*` instance methods to convert ORM models to
  domain models.
- Schemas translate between the HTTP interface and domain models: request
  schemas provide `to_*` instance methods, and response schemas provide
  `from_*` static methods.
- Domain models are frozen, immutable dataclasses.
- Tuples are the preferred collection type for domain and response values
  (e.g. `tuple[SubscriptionWithProduct, ...]`).

## Code style

- Use `id_` for function parameters to avoid shadowing the built-in `id`.

## Language style

Apply these rules in prose such as docstrings, documentation, and
comments, but not in code, paths, URLs, commands, or identifiers:

- Prefer short sentences over long sentences.
- Use the Oxford comma in lists of three or more items (e.g. "red, green,
  and blue" instead of "red, green and blue").
- Prefer "and" over slashes to express combinations (e.g. "red and blue"
  instead of "red/blue").
- Prefer "or" over slashes to express alternatives (e.g. "success or
  failure" instead of "success/failure").
- Prefer "or" over "and/or" (e.g. "success or failure" instead of
  "success and/or failure").

## Development tools

`trcks-example-fastapi` uses `uv` for managing dependencies and tools.

```shell
# Run the development server:
uv run fastapi dev
# Run linting and code formatting:
uv run pre-commit run --all-files
# Run static type checks:
uv run pyright
# Run unit tests:
uv run pytest
# Enforce rules for the imports within and between Python packages:
uv run import-linter lint
```

## Documentation requirements

- Keep `AGENTS.md`, `CONTRIBUTING.md`, and `README.md` up to date when
  architecture, tooling, or features change.
