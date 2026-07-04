# AI coding agent instructions for `trcks-example-fastapi`

## Project requirements

- `trcks-example-fastapi` is an example FastAPI application.
  It follows FastAPI best practices.
- `trcks-example-fastapi` demonstrates type-safe
  railway-oriented programming (ROP) with `trcks`.
  It returns domain errors instead of raising them.

## Architecture decisions

### Application layers

- The package `app` has two layers: `data_structures` and `logic`.
- `app.data_structures` contains data classes and models.
  It has two sublayers: ORM models and API schemas (at the same level),
  and domain classes below them.
- `app.logic` contains business logic and data access.
  It has five sublayers: the app entry point, routers, services,
  repositories, and the database.

### Data structures

- Collections of values are tuples (e.g. `tuple[SubscriptionWithProduct, ...]`).
- Domain models are frozen, immutable, and final data classes.
- ORM models and request schemas provide `to_*` methods
  that convert them to domain models.
- Response schemas provide `from_*` methods
  that convert domain models to response schemas.

### Business logic

- Public methods of repository and service classes return `trcks.AwaitableResult`
  or `trcks.AwaitableTuple` values (except for the `dummy` repository and service).
- Routers await service methods and handle the resulting `trcks.Result`:
  - `trcks.Success` values are returned with
    an appropriate HTTP success status code.
  - `trcks.Failure` payloads are mapped to an appropriate HTTP exception
    and raised.

### Import contracts

`tool.importlinter.contracts` in `pyproject.toml` must contain at least:

- `layers` contracts that restrict each layer to importing only
  the layers below it.
- `protected` contracts that restrict which modules in the same layer or
  a higher layer may import specific modules.
- `protected` contracts that restrict which internal modules may import
  specific external packages.

## Code style

- Use `id_` for function parameters to avoid shadowing the built-in `id`.

## Language style

Apply these rules in prose such as docstrings, documentation, and
comments, but not in code, paths, URLs, commands, or identifiers:

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

## Documentation requirements

- Keep `AGENTS.md`, `CONTRIBUTING.md`, and `README.md` up to date when
  architecture, tooling, or features change.
