# trcks-example-fastapi

Forget to handle one of your domain errors,
and your type checker reports the exact file and line —
before you run a single test.
This repository demonstrates that promise with an example FastAPI application
built on type-safe railway-oriented programming (ROP) with
[`trcks`](https://pypi.org/project/trcks/),
which represents every domain outcome as a `Success` or a `Failure`,
so domain errors travel in return values rather than exceptions.
The example domain is subscription management.

In a conventional FastAPI application, failures hide behind the signature:

```python
async def create_subscription(...) -> SubscriptionWithProduct: ...
# Also raises 404 and 409 exceptions. The signature does not tell.
```

With `trcks`, the same method declares every failure in its return type:

```python
def create_subscription(...) -> AwaitableResult[
    ProductNotSubscribableBecauseStatusError
    | ProductWithIdDoesNotExistError
    | SubscriptionWithIdAlreadyExistsError
    | UserWithIdDoesNotExistError,
    SubscriptionWithProduct,
]: ...
```

The section
[Explanation: The case for railway-oriented programming](#explanation-the-case-for-railway-oriented-programming)
shows how this makes error handling explicit, exhaustive, and testable.

**Who is this for?** Experienced FastAPI developers who want to
keep domain errors in their function signatures and
let the type checker enforce exhaustive error handling.

## How-to: Get the application running

1. Install [`uv`](https://docs.astral.sh/uv/) if you have not already done so.
2. Clone the `trcks-example-fastapi` repository and `cd` into it.
3. Start the development server by running `uv run fastapi dev`.
4. Open the interactive API documentation at <http://127.0.0.1:8000/docs> and
   explore the endpoints.

**Note:** The application creates its SQLite schema automatically on startup.
[The following tutorial](#tutorial-create-your-first-subscription)
populates it with sample data.

## Tutorial: Create your first subscription

This walkthrough creates a subscription from scratch,
starting with the product and user it needs.
It requires a running development server
(see [How-to: Get the application running](#how-to-get-the-application-running)).
Every request uses a fixed UUID, so rerunning the walkthrough returns
`409 Conflict` responses. To start over, stop the development server,
delete `database.sqlite3`, and then restart the development server.

First, create a published product:

```shell
curl --include \
  --header "Content-Type: application/json" \
  --data '{
    "id": "11111111-1111-4111-8111-111111111111",
    "monthly_fee_in_euros": "9.99",
    "name": "Pro Plan",
    "status": "published"
  }' \
  http://127.0.0.1:8000/products/
```

Then create a draft product:

```shell
curl --include \
  --header "Content-Type: application/json" \
  --data '{
    "id": "22222222-2222-4222-8222-222222222222",
    "monthly_fee_in_euros": "4.99",
    "name": "Beta Plan",
    "status": "draft"
  }' \
  http://127.0.0.1:8000/products/
```

Finally, create a user:

```shell
curl --include \
  --header "Content-Type: application/json" \
  --data '{
    "id": "33333333-3333-4333-8333-333333333333",
    "email": "ada@example.com"
  }' \
  http://127.0.0.1:8000/users/
```

With the product and user in place,
the example now follows two tracks: success and failure.

### Success track

Subscribe the user to the published product:

```shell
curl --include \
  --header "Content-Type: application/json" \
  --data '{
    "id": "44444444-4444-4444-8444-444444444444",
    "is_active": true,
    "user_id": "33333333-3333-4333-8333-333333333333",
    "product_id": "11111111-1111-4111-8111-111111111111"
  }' \
  http://127.0.0.1:8000/subscriptions/
```

A valid request returns `201 Created` with the new subscription:

```json
{
  "is_active": true,
  "id": "44444444-4444-4444-8444-444444444444",
  "product": {
    "monthly_fee_in_euros": "9.99",
    "name": "Pro Plan",
    "status": "published",
    "id": "11111111-1111-4111-8111-111111111111"
  }
}
```

### Failure track

Subscribe the user to the draft product:

```shell
curl --include \
  --header "Content-Type: application/json" \
  --data '{
    "id": "55555555-5555-4555-8555-555555555555",
    "is_active": true,
    "user_id": "33333333-3333-4333-8333-333333333333",
    "product_id": "22222222-2222-4222-8222-222222222222"
  }' \
  http://127.0.0.1:8000/subscriptions/
```

The product-status check creates a domain error,
which the router maps to `409 Conflict`:

```json
{
  "detail": "Product with ID 22222222-2222-4222-8222-222222222222 is in draft status."
}
```

Both tracks carry their outcome in the return type:
a value on success and a domain error on failure.
The following sections show how `trcks` makes that explicit, exhaustive, and testable.

## Explanation: The case for railway-oriented programming

In a **conventional FastAPI application**,
an endpoint that can fail raises an `HTTPException` deep in the call stack.
Alternatively, it raises a custom exception that an exception handler catches later.
Either way, the failure never shows up in the function signature.
A service method that returns `Subscription` gives no hint
that it can also raise an `HTTPException` with status code 404 or 409.
The failures travel as exceptions, so a caller might forget to handle one,
and the omission surfaces only at runtime.

**Railway-oriented programming (ROP)** puts every *domain* error in the return type.
Each operation runs on one of two tracks: the success track carries the value forward,
and the failure track short-circuits the remaining steps.
Technical errors, such as a lost database connection, still propagate as exceptions.
Because every domain error is part of the return type, the type checker knows
the exact union of failures. It flags every caller that fails to handle one of
them, so the failure paths become explicit, exhaustive, and testable.

The following table contrasts the two approaches at a glance:

| Question                                          | Exceptions  | Railway-oriented programming |
|---------------------------------------------------|-------------|------------------------------|
| Are domain errors visible in function signatures? | No.         | Yes.                         |
| Does the type checker catch unhandled errors?     | No.         | Yes.                         |
| When do you notice an unhandled error?            | At runtime. | At type-check time.          |

The `create_subscription` method in
[`subscription_service.py`](src/subscription_management/logic/services/subscription_service.py)
serves as the running example throughout this document.
It declares its four failure modes right in its signature:

```python
def create_subscription(
    self, subscription: SubscriptionWithUserIdAndProductId
) -> AwaitableResult[
    ProductNotSubscribableBecauseStatusError
    | ProductWithIdDoesNotExistError
    | SubscriptionWithIdAlreadyExistsError
    | UserWithIdDoesNotExistError,
    SubscriptionWithProduct,
]: ...
```

The router handles each failure explicitly.
The trailing `assert_never` makes exhaustiveness a static type-checking guarantee.

```python
match result:
    case ("failure", ProductNotSubscribableBecauseStatusError(...)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=...)
    case ("failure", ProductWithIdDoesNotExistError(...)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=...)
    case ("failure", SubscriptionWithIdAlreadyExistsError(...)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=...)
    case ("failure", UserWithIdDoesNotExistError(...)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=...)
    case ("success", subscription_response):
        return subscription_response
    case _:  # every failure above is handled, so this is unreachable
        assert_never(result)
```

**Try it yourself:**
Add a new domain error to the return type of `create_subscription` in
[`subscription_service.py`](src/subscription_management/logic/services/subscription_service.py).
Then run `uv run pyright`.
The new error now reaches the router unhandled,
so `assert_never(result)` no longer receives `Never`.
Pyright reports the exact file and line of the router that needs a new `case`.
You catch the gap before you run the application or write a test.

The rest of this document shows how the application delivers on that promise,
starting with its step composition.

## Explanation: Step composition with `trcks.oop.Wrapper`

The `create_subscription` method in
[`subscription_service.py`](src/subscription_management/logic/services/subscription_service.py)
composes its steps as follows:

```python
return (
    Wrapper(subscription)
    .tap_to_awaitable_result(self._read_product_and_check_status_is_published)
    .map_success_to_awaitable_result(
        self._subscription_repository.create_subscription
    )
    .core
)
```

The chain starts from the plain wrapped value.
`tap_to_awaitable_result` runs a check without changing the carried value.
Every subsequent `*_success_*` step runs only on the success track.
The `map_success_to_awaitable_result` method transforms the value on success.
The first failure short-circuits the remaining steps.
Each step can contribute its own domain error,
so the error union grows along the chain, and the type checker tracks it.
The final `.core` unwraps the `Wrapper` to a plain `trcks.AwaitableResult`.

Composition is not limited to the service layer.
The `create_subscription` endpoint in
[`subscription_router.py`](src/subscription_management/logic/routers/subscription_router.py)
builds a similar chain. It converts the request schema to a domain model with
`map`, calls the service with `map_to_awaitable_result`, and converts the
domain model to a response schema with `map_success`.
The repository classes compose their steps the same way; see the
[`trcks` documentation](https://christophgietl.github.io/trcks/) for
details on `Wrapper` and its methods.

## Explanation: Domain-error patterns

The router in
[`subscription_router.py`](src/subscription_management/logic/routers/subscription_router.py)
maps each domain error from `create_subscription` in
[`subscription_service.py`](src/subscription_management/logic/services/subscription_service.py)
to an appropriate HTTP exception. This section illustrates three patterns that
keep domain errors in the return type.

### Pass-through domain errors

Some domain errors travel unchanged from the repository to the router.
For example,
[`subscription_repository.py`](src/subscription_management/logic/repositories/subscription_repository.py)
creates a `SubscriptionWithIdAlreadyExistsError`, the service forwards it unchanged,
and the router maps it to an HTTP 409 exception.

### Service-layer domain errors

Other domain errors originate in the service layer as business-rule failures
rather than database facts.
For example, the product-status check in the chain
creates a `ProductNotSubscribableBecauseStatusError` when the product is not subscribable,
which the router maps to an HTTP 409 exception.

### Unions of domain errors

A single method may fail with several distinct domain errors.
The `create_subscription` method returns a union of
`ProductNotSubscribableBecauseStatusError`,
`ProductWithIdDoesNotExistError`,
`SubscriptionWithIdAlreadyExistsError`,
and `UserWithIdDoesNotExistError`
because each step of a `trcks.oop.Wrapper` chain can contribute its own
error, and the chain's generic type parameters track them all.
For example, the `_check_that_product_and_user_exist` helper in
[`subscription_repository.py`](src/subscription_management/logic/repositories/subscription_repository.py)
reads the product and then the user, contributing a
`ProductWithIdDoesNotExistError` and a `UserWithIdDoesNotExistError`,
respectively.
The type checker therefore knows the exact union of failures
(see [Explanation: The case for railway-oriented programming](#explanation-the-case-for-railway-oriented-programming))
and the router must handle every one of them.

## Reference: Application layers

The package
[`subscription_management.logic.routers`](src/subscription_management/logic/routers/)
contains FastAPI routers that call and await the service class methods.
Each router translates the awaited `trcks.Result` into an HTTP response.

The package
[`subscription_management.logic.services`](src/subscription_management/logic/services/)
contains service classes that implement business logic
on top of the repository classes.
Their public methods return `trcks.AwaitableResult` or `trcks.AwaitableTuple` values.

The package
[`subscription_management.logic.repositories`](src/subscription_management/logic/repositories/)
contains repository classes with public CRUD methods.
These methods return `trcks.AwaitableResult` or `trcks.AwaitableTuple` values.
