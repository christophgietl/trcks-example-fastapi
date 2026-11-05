# Coding agent instructions for `trcks-example-fastapi`

## Project requirements

The repository `trcks-example-fastapi` contains an example application that
follows FastAPI best practices and
demonstrates type-safe railway-oriented programming (ROP) with `trcks`.
It returns domain errors instead of raising them.

## Project decisions

- The example application lives in the _subscription management_ domain.

## Architecture decisions

### Import contracts

The section `tool.importlinter.contracts` in [pyproject.toml](pyproject.toml)
must contain at least:

- exhaustive `layers` contracts that restrict each layer
  to importing only the layers below it
- `protected` contracts that restrict which modules may import
  specific modules, subpackages, or external packages

### Data structures

- Collections of values are tuples (e.g. `tuple[SubscriptionWithProduct, ...]`).
- Domain models are frozen and immutable data classes.
  If public, they are also final.
- Domain errors are frozen dataclasses defined in a dedicated `*_error`
  module next to their entity (e.g. `ProductWithIdDoesNotExistError` in
  `subscription_management.data_structures.domain.product_error`).
  Each error carries at least the relevant identifier (e.g. `id`, `email`, or `name`).
- ORM models use SQLAlchemy's declarative dataclass mapping style
  (i.e. `DeclarativeBase` combined with `MappedAsDataclass`).
- ORM models and request schemas provide `to_*` methods
  that convert them to domain models.
- Response schemas provide `from_*` methods (except for `HealthResponse`).
  These methods convert domain models to response schemas.

### Logic

- Repository classes handle all database operations.
  They use SQLAlchemy's ORM-enabled delete, insert, select, and update syntax
  and `sqlalchemy.ext.asyncio.AsyncSession.get` (except for `DummyRepository`).
- Service classes handle all business logic.
- Public repository and service methods take
  `str` values, `uuid.UUID` values, domain models, or no arguments.
  They return domain models wrapped in `trcks.AwaitableResult` or `trcks.AwaitableTuple`
  (except for `DummyRepository` and `DummyService`).
- Routers await service methods and handle their output:
  - They return `trcks.Success` payloads with
    an appropriate HTTP success status code.
  - They map `trcks.Failure` payloads to appropriate HTTP exceptions and raise them.

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
  (e.g. "a user or a product" instead of "a user and/or a product").

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
# Run tests:
uv run pytest
# Enforce import rules:
uv run import-linter lint
# Install a library skill:
uv run library-skills install --skill fastapi --yes
```

## Testing strategy

- Prefer integration tests.
- Cover every router and endpoint.
- Assert on HTTP responses and, where applicable, database side effects.
- Data-structure tests exercise ORM models directly
  (e.g. foreign key constraints and cascade deletes).
- Test coverage must stay at 100% (`--cov-fail-under=100`).

## Documentation requirements

- Write documentation for experienced FastAPI developers.
- Excite interest in ROP and convey its advantages.
- Use the `create_subscription` flow as a running example in [README.md](README.md).
- Start every level 2 headline in [README.md](README.md) and
  [CONTRIBUTING.md](CONTRIBUTING.md) with a Diátaxis prefix
  (i.e. `Tutorial:`, `How-to:`, `Reference:`, or `Explanation:`).
- Keep [this file](AGENTS.md), [CONTRIBUTING.md](CONTRIBUTING.md), and
  [README.md](README.md) up to date when architecture, tooling, features, or
  implementation change.
