# Copilot Instructions for trcks-example-fastapi

## Architecture Overview

This FastAPI application follows a strict layered architecture pattern:

- **Routers Layer** (`app/logic/routers/`): FastAPI routers defining HTTP endpoints
- **Schemas Layer** (`app/data_structures/schemas/`): Pydantic models for HTTP interface
- **Services Layer** (`app/logic/services/`): Business logic orchestration
- **Repositories Layer** (`app/logic/repositories/`): Data access abstractions
- **Domain Layer** (`app/data_structures/domain/`): Immutable domain models
- **ORM Layer** (`app/data_structures/models.py`): SQLAlchemy models

**Critical Rule**:
A layer only imports from itself or lower layers.
Never import upwards (e.g. services importing from routers).
Circular import pressure should be resolved via moving shared concepts downward.

### Import-Linter Enforcement

The architecture is enforced by import-linter with the following contracts (see `pyproject.toml`):

**Layer Contract**: `app.main` → `app.logic.routers` → `app.logic.services`
→ `app.logic.repositories` → `app.data_structures` (strict ordering)

**Protected Modules**:
- `app.database` – only importable by `app.main` and `app.logic.repositories`
- `app.data_structures.domain` – only importable
    by `app.data_structures.models`,
    `app.logic.repositories`,
    `app.data_structures.schemas`, and
    `app.logic.services`
- `app.data_structures.models` – only importable by `app.database` and `app.logic.repositories`
- `app.data_structures.schemas` – only importable by `app.logic.routers`

**Independence Contracts**:
- All routers are independent (cannot import each other)
- All services are independent (cannot import each other)

## Key Patterns

### Functional Error Handling with `trcks`

All business operations use `trcks.Result` / `AwaitableResult`
for explicit success/failure modeling.

Async create example (mirrors current implementation style):

```python
from typing import Literal
from trcks.oop import Wrapper
from trcks import AwaitableResult

from app.data_structures.domain import User
from app.logic.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, repo: UserRepository):
        self._repo = repo

    def create_user(
            self, user: User
    ) -> AwaitableResult[Literal["Email already exists", "ID already exists"], None]:
        return self._repo.create_user(user)


# Router layer (pattern)
match result:  # result: Result[...]
    case ("failure", "Email already exists"):
        raise HTTPException(
            status_code=409, detail=f"User with email {email} already exists",
        )
    case ("failure", "ID already exists"):
        raise HTTPException(
            status_code=409, detail=f"User with ID {user_id} already exists",
        )
    case ("success", payload):  # payload is None for create in current code
        return payload  # (Create endpoint presently returns 201 with empty body)
    case _:
        assert_never(result)
```

Important helper methods you will see:
- `.map(...)`, `.map_success(...)` – transform success values
- `.map_to_result(...)`, `.map_to_awaitable_result(...)` –
    lift function / coroutine returning `Result`
- `.tap_to_awaitable_result(...)`, `.tap_success_to_awaitable_result(...)` –
    execute side-effect returning `AwaitableResult` (used for foreign key pre-validation)
- `AwaitableWrapper(...)` – adapt awaitables into the fluent mapping chain

### Data Flow Pattern

General ideal round trip:
1. API Schema → Domain Model → DB Model → Domain Model → API Schema

Current deviations:
- Create user endpoint returns `None` on success (201 No Content).
    It stops after persistence (DB Model) and
    does not remap back to a domain/API response.
    Reads/updates follow the full cycle.

If you later decide to return the created resource,
adjust repository `create_user` to return the stored `User` (or refetch),
and update service + router mapping accordingly.

### Domain Models

Domain models are frozen dataclasses (immutability and hashability).

**User** dataclass with required `id` and `email`.

**Product** dataclass with `id`, `name`, `monthly_fee_in_euros`, and `status`.
Status values: `"draft"`, `"published"`, `"deprecated"`.

**SubscriptionWithProduct** dataclass with `id`, `is_active`,
and nested `product` (Product).
**SubscriptionWithUserIdAndProductId** dataclass with `id`, `is_active`,
`user_id`, and `product_id` (for creation without nested objects).

Collections are typed as immutable tuples: `Users`, `Products`,
`Subscriptions`, etc.

Earlier design ideas ("UserWithOptionalId" vs "UserWithRequiredID") are not implemented.
If you reintroduce optional IDs (e.g., server-generated UUIDs),
add separate dataclasses and explicit conversion functions.

### ORM Bidirectional Conversion Pattern

All ORM models in `app/data_structures/models.py` implement bidirectional conversion:

**Domain → ORM**: Static method `from_*`
  (e.g., `UserModel.from_user(user: User)`,
    `SubscriptionModel.from_subscription_with_user_id_and_product_id(...)`)
**ORM → Domain**: Instance method `to_*` (e.g., `user_model.to_user_with_subscriptions_with_products()`)

This pattern ensures explicit, type-safe conversions between layers.

### Mapping Functions

Explicit mappers convert between:
- API Schema ↔ Domain (methods like `PostUserRequest.to_user(...)`, `PutUserRequest.to_user(id_)`)
- Domain ↔ DB (via ORM model methods: `UserModel.from_user(...)`, `UserModel.to_user_with_subscriptions_with_products(...)`)

Collections of domain objects are converted to tuples for immutability.

### Repository Layer Conventions

- Class-based repositories (e.g., `UserRepository`) wrap an injected `AsyncSession`.
- Method naming is direct (verb + noun):
    `create_user`, `read_user_by_id`, `read_users`, `update_user`, `delete_user`
    (no `db_` prefix despite earlier guideline drafts).
- Methods return `Result[...]` (or plain domain tuples) consistent with service expectations.

### Service Layer Conventions

- Thin orchestration over repositories, preserving `Result` semantics.
- Uses `AwaitableResult` type hints for async failures/successes.
- Avoids importing API schemas (maintains downward dependency direction).

### Error String Literals

Failure branches standardize on specific string literals.
Keep them centralized and consistent—changes require updating all match statements.

**User failures**:
- `"User does not exist"`
- `"Email already exists"`
- `"ID already exists"`

**Product failures**:
- `"Product does not exist"`
- `"Name already exists"`
- `"ID already exists"`
- `"Product status is published"`
- `"Product status is deprecated"`
- `"Cannot modify non-status attributes of a published product"`
- `"Cannot modify non-status attributes of a deprecated product"`
- `"Cannot change status from published to draft"`
- `"Cannot change status from deprecated to draft"`
- `"Cannot change status from deprecated to published"`

**Subscription failures**:
- `"Subscription does not exist"`
- `"ID already exists"`
- `"Product does not exist"` (foreign key validation)
- `"User does not exist"` (foreign key validation)

## Database Setup

- SQLite via `sqlalchemy[aiosqlite]` driver URL: `sqlite+aiosqlite:///database.sqlite3`
- All ORM models live in a single file: `app/data_structures/models.py`
- Internal declarative base: `_BaseModel` (inherits `DeclarativeBase`, `MappedAsDataclass`)
- Table creation occurs at startup inside the FastAPI `lifespan` context
    (see `app/data_structures/models.py#set_pragmas_and_create_all_tables`
      used by `app/database.py` and registered in `app/main.py`).
- SQLite foreign key enforcement enabled via `PRAGMA foreign_keys=ON`
    at connection time.

## Dependency Injection Pattern

- `Annotated[T, Depends(...)]` aliases
    (e.g., `AsyncSessionDep`, `UserRepositoryDep`, `UserServiceDep`)
    provide strongly typed dependencies.
- Use the `type` keyword for these dependency aliases.

## Development Workflow

### Running the Application

```bash
fastapi dev                # Auto-detects app/main.py:app
# or
uvicorn app.main:app --reload
```

### Code Quality Tools

```bash
pyright          # Strict type checking
ruff check       # Lint (ALL rules except configured ignores)
ruff format      # Auto-format
```

### Project Structure Notes

- Dependency management:
    `uv` with exact version pinning (`[tool.uv] add-bounds = "exact"`)
- Python version: 3.14 (see `requires-python ==3.14.*` in pyproject.toml)
- Tests present under `tests/` (pytest + pytest-asyncio)

## Conventions & Style

- Use `id_` for function parameters to avoid shadowing Python built-in `id`.
- Router prefixes: `/users`, `/products`, `/subscriptions`, `/health`.
- Explicit `status_code` and response documentation in decorator metadata.
- Domain & response collection types prefer immutable tuples.
- Keep mapping functions small and pure.
- Maintain forward-only dependency direction.

## Adding New Features (Checklist)

1. Domain: Add / update dataclass in `app/data_structures/domain/`.
2. Persistence: Add / update SQLAlchemy model(s)
    in `app/data_structures/models.py` &
    repository method(s) in `app/logic/repositories/`.
3. Service: Add orchestration method returning appropriate `Result` or value.
4. API Schemas: Add Pydantic request/response models + mapping helpers in `app/data_structures/schemas/`.
5. Router: Implement endpoint in `app/logic/routers/` with pattern-matching
     on `Result` failures.
6. Main: Register new router in `app/main.py`.
7. Tests: Add / update tests in `tests/` to cover success + failure cases.

## Evolving the Create Pattern (Optional Improvement)

If you want POST /users to echo the created resource:
- Change repository `create_user` to return the inserted `User` (model → domain)
    on success instead of `None`.
- Adjust service & router to map success payload to `UserResponse`.
- Update OpenAPI response schema accordingly.

## Common Pitfalls

- Forgetting to update all match arms when adding/modifying failure literals.
- Importing routers/schemas layer types into services or repositories
    (violates layering rule).
- Returning mutable sequences where immutable tuples are expected
    (breaks type alias expectations like `Users`).
- Swallowing IntegrityError patterns other than the known unique constraints.

## Testing Guidelines

- Cover both success and each distinct failure literal for new operations.
- Use pytest async tests with `asyncio_mode = auto` (see pyproject config).
- Avoid DB state leakage:
    rely on test database or transaction rollbacks if you introduce more fixtures.

## Style / Tooling Configuration Summary

- Pyright strict mode with extra diagnostics (see `[tool.pyright]`).
- Ruff enforces almost all rules;
    docstring rules disabled (`D`),
    conflict-prone rules ignored (`COM812`, `TC001`, `TC003`).
- Keep new lint ignores minimal; justify via inline comments.

## Glossary

- Result / AwaitableResult:
    Tuple-based discriminated union: `("success", value)` or `("failure", error_literal)`.
- Wrapper / AwaitableWrapper:
    Helpers from `trcks.oop` enabling fluent functional transformations.
- Mapping Function: Pure function converting between layers (API ↔ Domain ↔ DB).

## Future Extensions (Ideas)

(Not implemented—document here if adopted.)
- Separate `UserWithOptionalId` for server-generated IDs.
- Generic repository base class for CRUD patterns.
- Structured error codes instead of string literals.
- Pagination for `read_users`.

## Keep Documentation Updated

This project maintains three documentation files that must stay synchronized
as the codebase evolves: README.md (user-facing quickstart),
CONTRIBUTING.md (developer onboarding), and this file (AI assistant context).

### When to Update README.md

- Update when adding, removing, or renaming major application directories
  (repositories, services, routers).
- Update when changing the startup command or installation process.
- Update when modifying the core architectural pattern or
  Result/AwaitableResult flow.
- Update when adding new major features that change the project's demonstrated purpose.

### When to Update CONTRIBUTING.md

- Update when adding or removing development tools (linters, formatters, test frameworks).
- Update when changing dependency management approach or setup steps.
- Update when modifying command-line tool syntax or adding new commands.
- Update when changing pre-commit hooks or other developer workflow automation.

### When to Update copilot-instructions.md

- Update whenever behavior diverges from documented patterns
  (e.g., returning resources on create, adding optional IDs,
    splitting models into a package).
- Update when introducing new architectural layers or changing layer import rules.
- Update when adding new error literals or modifying error handling patterns.
- Update when implementing ideas from "Future Extensions" or removing "Optional Improvements."
- Update when changing ORM models, domain models, or their conversion patterns.
- Update when modifying repository method signatures or service orchestration patterns.

### Cross-Document Consistency

Maintain consistency across these overlapping concerns:
- Development commands in copilot-instructions.md "Development Workflow"
  must match those in CONTRIBUTING.md "Usage."
- README.md "Project Structure" should be the simplified version of
  copilot-instructions.md "Architecture Overview."
- Tool configuration changes in pyproject.toml should be reflected in both
  CONTRIBUTING.md (usage commands) and
  copilot-instructions.md (Style/Tooling Configuration Summary).
- Import rules in copilot-instructions.md "Import-Linter Enforcement"
  must match actual contracts in pyproject.toml and be executable
  via CONTRIBUTING.md's `lint-imports` command.
