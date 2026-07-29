# AI coding agent instructions for `trcks-example-fastapi`

## Project requirements

- `trcks-example-fastapi` is an example FastAPI application demonstrating
  type-safe railway-oriented programming (ROP) with `trcks`; it follows
  FastAPI best practices and returns domain errors instead of raising them.

## Project decisions

- The example domain _subscription management_ illustrates ROP in FastAPI.

## Architecture decisions

### Application layers

The package `subscription_management` has three layers:

- `testing`: test helpers
- `logic`: app entry point, routers, services, repositories, database
  (five sublayers)
- `data_structures`: ORM models and API schemas, domain classes
  (two sublayers)

### Data structures

- Collections of values are tuples
  (e.g. `tuple[SubscriptionWithProduct, ...]`).
- Public domain models are frozen, immutable, and final data classes.
- Domain errors are frozen dataclasses defined in a dedicated `*_error`
  module next to their entity (e.g. `ProductWithIdDoesNotExistError` in
  `subscription_management.data_structures.domain.product_error`); each
  error carries the relevant identifier (`id`, `email`, or `name`).
- ORM models use SQLAlchemy's declarative dataclass mapping style
  (i.e. `DeclarativeBase` combined with `MappedAsDataclass`).
- ORM models and request schemas provide `to_*` methods that convert to
  domain models; response schemas provide `from_*` methods (except for
  `HealthResponse`) that convert domain models to response schemas.

### Logic

- Repository classes handle all database operations. They use SQLAlchemy's
  ORM-enabled delete, insert, select, and update methods as well as
  `AsyncSession.get` (except for `DummyRepository`).
- Service classes handle all business logic.
- Public methods of repository and service classes take `str` values,
  `uuid.UUID` values, domain models, or no arguments; they return domain
  models wrapped in `trcks.AwaitableResult` or `trcks.AwaitableTuple`
  (except for the `DummyRepository` and `DummyService`).
- Routers await service methods, returning `trcks.Success` values with an
  appropriate HTTP status code and mapping `trcks.Failure` payloads to an
  HTTP exception that is then raised.

### Import contracts

`tool.importlinter.contracts` in `pyproject.toml` must contain at least:
`layers` contracts that restrict each layer to importing only the layers
below it; `protected` contracts that restrict which modules in the same
layer or a higher layer may import specific modules; and `protected`
contracts that restrict which internal modules may import specific external
packages.

## Code style

- Sort functions, type aliases, and methods case-insensitively in
  alphabetical order within each module or class (functions in router
  modules excepted).
- Place comments regarding implementation inside the respective function
  or class, not above it.
- Quote type expressions in `typing.cast` calls
  (e.g. `cast("int", my_number)`).
- Suppress `ruff` rule `TC001` when importing a `*Dep` type:

  ```python
  from subscription_management.logic.repositories.product_repository import (
      ProductRepositoryDep,  # noqa: TC001
  )
  ```

## Language style

Apply these rules in prose such as docstrings, documentation, and
comments, but not in code, paths, URLs, commands, or identifiers:

- Prefer active voice over passive voice
  (e.g. "No module may import X" instead of "X may not be imported").
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
uv run fastapi dev
uv run pre-commit run --all-files             # all hooks
uv run pre-commit run --all-files ruff-check  # one hook
uv run pyright
uv run pytest
uv run import-linter lint
```

## Testing strategy

- Prefer integration tests covering every router and endpoint (asserting
  HTTP responses and, where applicable, database side effects);
  data-structure tests exercise ORM models directly
  (e.g. foreign key constraints and cascade deletes).
- Test coverage must stay at 100% (`--cov-fail-under=100`).

## Documentation requirements

- Keep `AGENTS.md`, `CONTRIBUTING.md`, and `README.md` up to date when
  architecture, tooling, features, or implementation change.
- Write for experienced FastAPI developers; excite interest in ROP and
  convey its advantages.
- Use the `create_subscription` flow as a running example in `README.md`.
- Start every level 2 headline in `README.md` and `CONTRIBUTING.md` with a
  Diátaxis prefix (i.e. `Tutorial:`, `How-to:`, `Reference:`, or `Explanation:`).
