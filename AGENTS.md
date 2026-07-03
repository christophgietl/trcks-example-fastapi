# AI coding agent instructions for `trcks-example-fastapi`

## Project requirements

- `trcks-example-fastapi` is an example FastAPI application
  demonstrating type-safe railway-oriented programming (ROP) with `trcks`.
- Business operations return domain errors instead of raising them.

## Architecture decisions

### Layers

- Routers (`app/logic/routers/`): FastAPI routers defining HTTP endpoints.
- Schemas (`app/data_structures/schemas/`): Pydantic models for the HTTP interface.
- Services (`app/logic/services/`): Business logic orchestration.
- Repositories (`app/logic/repositories/`): data access abstractions.
- Domain (`app/data_structures/domain/`): immutable domain models.
- ORM (`app/data_structures/models.py`): SQLAlchemy models.

A layer only imports from itself or lower layers.
Never import upwards (e.g. services importing from routers).
Import-linter contracts in `pyproject.toml` enforce
this layer order and additional protections:

- `app.database` is only importable by `app.main` and `app.logic.repositories`.
- `app.data_structures.domain` is only importable by
  `app.data_structures.models`, `app.data_structures.schemas`,
  `app.logic.repositories`, and `app.logic.services`.
- `app.data_structures.models` is only importable by
  `app.database` and `app.logic.repositories`.
- `app.data_structures.schemas` is only importable by `app.logic.routers`.
- Routers are independent of each other; services are independent of each other.

### Core patterns

- Use `trcks.Result` and `trcks.AwaitableResult`
  for explicit success or failure return types.
- Routers pattern-match on `Result` values:
  map `Failure` errors to `HTTPException`s and
  return `Success` payloads with an appropriate HTTP status code.
- ORM models provide bidirectional conversion:
  `from_*` static methods (domain to ORM) and
  `to_*` instance methods (ORM to domain).
- Domain models are frozen, immutable dataclasses;
  collections use immutable tuples (e.g. `Users`, `Products`).
- Failure literals are centralized strings
  (e.g. `"User does not exist"`, `"Email already exists"`).
  Update every match statement when adding or changing a failure literal.
- Dependencies are injected via
  `Annotated[T, Depends(...)]` type aliases (e.g. `UserServiceDep`).

## Code style

- Use `id_` for function parameters to avoid shadowing the built-in `id`.
- Keep mapping functions between layers small and pure.
- Prefer immutable tuples over mutable sequences for domain and response collections.

## Language style

Apply these rules in prose such as docstrings, documentation, and comments,
but not in code, paths, URLs, commands, or identifiers:

- Use the Oxford comma in lists of three or more items
  (e.g. "red, green, and blue" instead of "red, green and blue").
- Prefer "and" over slashes to express combinations
  (e.g. "red and blue" instead of "red/blue").
- Prefer "or" over slashes to express alternatives
  (e.g. "success or failure" instead of "success/failure").
- Prefer "or" over "and/or"
  (e.g. "success or failure" instead of "success and/or failure").
- Prefer short sentences over long ones.

## Development tools

`trcks-example-fastapi` uses `uv` for managing dependencies and tools.

```shell
# Run the development server:
uv run fastapi dev
# Run linting and code formatting:
uv run pre-commit run --all-files
# Run static type checks:
uv run pyright
# Run unit tests and doctests:
uv run pytest
# Enforce rules for the imports within and between Python packages:
uv run import-linter lint
```

## Testing strategy

- Use pytest with async tests (`anyio_mode = "auto"`).
- 100% test coverage is required (`--cov-fail-under=100`).
- Cover both the success case and each distinct failure literal for new operations.

## Documentation requirements

- Keep `AGENTS.md` up to date when architecture or tooling changes.
- Keep `CONTRIBUTING.md` up to date when tooling changes.
- Keep `README.md` up to date when features or project structure change.
- `.github/copilot-instructions.md` is a symlink to this file;
  do not maintain it separately.
