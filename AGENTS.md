# AI coding agent instructions for `trcks-example-fastapi`

## Project requirements

- `trcks-example-fastapi` is an example FastAPI application.
  It follows FastAPI best practices.
- `trcks-example-fastapi` demonstrates type-safe
  railway-oriented programming (ROP) with `trcks`.
  It returns domain errors instead of raising them.

## Project decisions

- The example domain _subscription management_ illustrates ROP in FastAPI.

## Architecture decisions

### Application layers

- The package `subscription_management` has three layers: `testing`, `logic`,
  and `data_structures`.
- `subscription_management.testing` contains test helpers.
- `subscription_management.logic` contains business logic and data access.
  It has five sublayers: the app entry point, routers, services,
  repositories, and the database.
- `subscription_management.data_structures` contains data classes and models.
  It has two sublayers: ORM models and API schemas at one level,
  and domain classes at the level below.

### Data structures

- Collections of values are tuples (e.g. `tuple[SubscriptionWithProduct, ...]`).
- Public domain models are frozen, immutable, and final data classes.
- Domain errors are frozen dataclasses defined in a dedicated `*_error`
  module next to their entity (e.g. `ProductWithIdDoesNotExistError` in
  `subscription_management.data_structures.domain.product_error`).
  Each error carries the relevant identifier (`id`, `email`, or `name`).
- ORM models use SQLAlchemy's declarative dataclass mapping style
  (i.e. `DeclarativeBase` combined with `MappedAsDataclass`).
- ORM models and request schemas provide `to_*` methods
  that convert them to domain models.
- Response schemas provide `from_*` methods (except for `HealthResponse`)
  that convert domain models to response schemas.

### Logic

- Repository classes handle all database operations.
  They use SQLAlchemy's ORM-enabled delete, insert, select, and update methods
  as well as `AsyncSession.get` (except for `DummyRepository`).
- Service classes handle all business logic.
- Public methods of repository and service classes take
  `str` values, `uuid.UUID` values, domain models, or no arguments.
  They return domain models wrapped in `trcks.AwaitableResult` or `trcks.AwaitableTuple`
  (except for the `DummyRepository` and `DummyService`).
- Routers await service methods. They handle awaited `trcks.Result` as follows:
  - `trcks.Success` values are returned with
    an appropriate HTTP success status code.
  - `trcks.Failure` payloads are mapped to an appropriate HTTP exception,
    which is then raised.

### Import contracts

`tool.importlinter.contracts` in `pyproject.toml` must contain at least:

- `layers` contracts that restrict each layer to importing only
  the layers below it.
- `protected` contracts that restrict which modules in the same layer or
  a higher layer may import specific modules.
- `protected` contracts that restrict which internal modules may import
  specific external packages.

## Code style

- Sort functions case-insensitively in alphabetical order within each module,
  except for router modules.
- Sort type aliases case-insensitively in alphabetical order within each module.
- Sort methods case-insensitively in alphabetical order within each class.
- Place comments regarding implementation inside the respective function or class,
  not above it.
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
# Run the development server:
uv run fastapi dev
# Run linting and code formatting (incl. ruff and rumdl):
uv run pre-commit run --all-files             # all hooks
uv run pre-commit run --all-files ruff-check  # one hook
# Run static type checks:
uv run pyright
# Run unit tests:
uv run pytest
# Enforce rules for the imports within and between Python packages:
uv run import-linter lint
```

## Testing strategy

- Prefer integration tests. They must cover every router and endpoint,
  asserting on HTTP responses and, where applicable, database side effects.
- Data-structure tests exercise ORM models directly
  (e.g. foreign key constraints and cascade deletes).
- Test coverage must stay at 100% (`--cov-fail-under=100`).

## Documentation requirements

- Keep `AGENTS.md`, `CONTRIBUTING.md`, and `README.md` up to date when
  architecture, tooling, or features change.

### `README.md`

- `README.md` targets experienced FastAPI developers.
- It excites interest in railway-oriented programming and conveys its advantages.
- It uses the `create_subscription` flow as a running example.
