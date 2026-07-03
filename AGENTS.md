# AI coding agent instructions for `trcks-example-fastapi`

## Project requirements

- `trcks-example-fastapi` is an example FastAPI application
  demonstrating type-safe railway-oriented programming (ROP) with `trcks`.
- Domain errors are returned, not raised.

## Architecture decisions

### Layers

- Routers (`app/logic/routers/`) define HTTP endpoints.
- Schemas (`app/data_structures/schemas/`) model the HTTP interface.
- Services (`app/logic/services/`) orchestrate business logic.
- Repositories (`app/logic/repositories/`) encapsulate data access.
- Domain (`app/data_structures/domain/`) holds immutable domain models.
- ORM models live in `app/data_structures/models.py`.

A layer may import only itself or lower layers. Import-linter contracts in
`pyproject.toml` enforce this order and additional guards, such as
`app.database` being importable only by `app.main` and
`app.logic.repositories`, and `app.data_structures.schemas` only by
`app.logic.routers`.

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
- Use immutable tuples for domain and response collections (e.g.
  `tuple[SubscriptionWithProduct, ...]`).
- Failure literals are `Literal` string types returned by repositories and
  services and matched in routers (e.g. `"User does not exist"`,
  `"Email already exists"`). Update every match statement when adding or
  changing a failure literal.
- Dependencies are injected via `Annotated[T, Depends(...)]` type aliases
  (e.g. `UserServiceDep`).

## Code style

- Use `id_` for function parameters to avoid shadowing the built-in `id`.

## Language style

Apply these rules in prose such as docstrings, documentation, and comments,
but not in code, paths, URLs, commands, or identifiers:

- Prefer short sentences over long sentences.
- Use the Oxford comma in lists of three or more items
  (e.g. "red, green, and blue" instead of "red, green and blue").
- Prefer "and" over slashes to express combinations
  (e.g. "red and blue" instead of "red/blue").
- Prefer "or" over slashes to express alternatives
  (e.g. "success or failure" instead of "success/failure").
- Prefer "or" over "and/or"
  (e.g. "success or failure" instead of "success and/or failure").

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

## Testing strategy

- Use pytest with async tests (`anyio_mode = "auto"`).
- Maintain 100% test coverage (`--cov-fail-under=100`).
- Cover both the success case and each distinct failure literal for new operations.

## Documentation requirements

- Keep `AGENTS.md`, `CONTRIBUTING.md`, and `README.md` up to date when
  architecture, tooling, or features change.
- `.github/copilot-instructions.md` is a symlink to this file; do not
  maintain it separately.
