# trcks-example-fastapi

This repository contains an example FastAPI application
that demonstrates type-safe railway-oriented programming with
[`trcks`](https://pypi.org/project/trcks/).
The example domain is subscription management.

## Why railway-oriented programming?

In a conventional FastAPI application, an endpoint that can fail
raises an `HTTPException` deep in the call stack,
or it raises a custom exception that an exception handler catches later.
Either way, the failure never shows up in the function signature.
A service method that returns `Subscription`
gives no hint that it can also produce a 404 or a 409.
The failure paths travel as exceptions, so a caller can forget to handle one,
and the omission surfaces only at runtime.

Railway-oriented programming (ROP) puts every *domain* error in the return type.
Each operation runs on one of two tracks:
the success track carries the value forward,
and the failure track short-circuits the remaining steps.
Technical errors, such as a lost database connection,
still propagate as exceptions.
Because every domain error is part of the return type,
the type checker knows the exact union of possible failures,
and it flags every caller that fails to handle one of them.
The failure paths become explicit, exhaustive, and testable.

For example, the service method that creates a subscription
declares its four failure modes right in its signature:

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
The trailing `assert_never` makes exhaustiveness a static type-checking guarantee:
add a new domain error to the union,
and the type checker reports every router that does not yet handle it.

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

The rest of this document walks through the same running example in detail.

## Project structure

The package
[`subscription_management.logic.routers`](src/subscription_management/logic/routers/)
contains FastAPI routers that call and await the service class methods.
Each router translates the awaited `trcks.Result` into an HTTP response.

The package
[`subscription_management.logic.services`](src/subscription_management/logic/services/)
contains service classes that implement business logic on top of the repository
classes.
Their public methods return `trcks.AwaitableResult` or `trcks.AwaitableTuple` values.

The package
[`subscription_management.logic.repositories`](src/subscription_management/logic/repositories/)
contains repository classes with public CRUD methods.
These methods return `trcks.AwaitableResult` or `trcks.AwaitableTuple` values.

## Composing steps with `trcks.oop.Wrapper`

The `create_subscription` method of the service class in
[`subscription_management.logic.services.subscription_service`](src/subscription_management/logic/services/subscription_service.py)
serves as a running example.
Its `trcks.oop.Wrapper` chain composes the steps
into a single flat pipeline:

```python
return (
    Wrapper(subscription)
    .tap_to_awaitable_result(self._read_product_and_check_status)
    .map_success_to_awaitable_result(
        self._subscription_repository.create_subscription
    )
    .core
)
```

Every step runs only on the success track.
`tap_to_awaitable_result` runs a check without changing the carried value,
and `map_success_to_awaitable_result` transforms the value on success.
The first failure short-circuits the remaining steps.
Each step can contribute its own domain error,
so the error union grows along the chain,
and the type checker tracks it.
The final `.core` unwraps the `Wrapper` to a plain `trcks.AwaitableResult`.

## Domain-error patterns

The router in
[`subscription_management.logic.routers.subscription_router`](src/subscription_management/logic/routers/subscription_router.py)
maps each domain error from `create_subscription`
to an appropriate HTTP exception.
The following subsections use this flow to illustrate three patterns,
each keeping domain errors in the return type.

### Pass-through domain errors

Some domain errors travel unchanged from the repository to the router.
For example,
[`subscription_management.logic.repositories.subscription_repository`](src/subscription_management/logic/repositories/subscription_repository.py)
creates a `SubscriptionWithIdAlreadyExistsError`,
the service forwards it unchanged,
and the router maps it to an HTTP 409 exception.

### Service-layer domain errors

Other domain errors originate in the service layer as business-rule failures
rather than database facts.
For example, the product-status check in the chain
creates a `ProductNotSubscribableBecauseStatusError`
when the product is not subscribable,
which the router maps to an HTTP 409 exception.

### Unions of domain errors

A single method may fail with several distinct domain errors.
The `create_subscription` method returns a union of
`ProductNotSubscribableBecauseStatusError`,
`ProductWithIdDoesNotExistError`,
`SubscriptionWithIdAlreadyExistsError`, and
`UserWithIdDoesNotExistError`.
Such a union arises because each step of a `trcks.oop.Wrapper` chain
can contribute its own domain error,
and the generic type parameters of `trcks.oop.Wrapper` track them all.
For example, the `_check_that_product_and_user_exist` helper in
`subscription_repository`
reads the product and then the user,
contributing a `ProductWithIdDoesNotExistError`
and a `UserWithIdDoesNotExistError` respectively.
As a result, the static type checker knows the exact union of failures
(see [Why railway-oriented programming?](#why-railway-oriented-programming)),
so the router must handle every one of them.

## Running the example application

1. Install `uv` if you have not already done so.
2. Clone the `trcks-example-fastapi` repository and `cd` into it.
3. Start the development server by running `uv run fastapi dev`.

*Note:* The repository includes a pre-configured SQLite database.
No additional setup is required.
