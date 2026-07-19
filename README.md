# trcks-example-fastapi

This repository contains an example FastAPI application
that demonstrates type-safe railway-oriented programming with
[`trcks`](https://pypi.org/project/trcks/).
The example domain is subscription management.

## Running the example application

1. Install `uv` if you have not already done so.
2. Clone the `trcks-example-fastapi` repository and `cd` into it.
3. Start the development server by running `uv run fastapi dev`.

*Note:* The repository includes a pre-configured SQLite database.
No additional setup is required.

## Project structure

The package
[`subscription_management.logic.repositories`](src/subscription_management/logic/repositories/)
contains repository classes with public CRUD methods.
These methods return `trcks.AwaitableResult` or `trcks.AwaitableTuple` values.

The package
[`subscription_management.logic.services`](src/subscription_management/logic/services/)
contains service classes that implement business logic on top of the repository
classes.
Their public methods return `trcks.AwaitableResult` or `trcks.AwaitableTuple` values.

The package
[`subscription_management.logic.routers`](src/subscription_management/logic/routers/)
contains FastAPI routers that call and await the service class methods.
Awaited `trcks.Result` values are then handled as follows:
The payload of `trcks.Success` values is returned.
The payload of `trcks.Failure` values is mapped to an appropriate
HTTP exception, which is then raised.

## Railway-oriented programming patterns

The `create_subscription` method of the service class in
[`subscription_management.logic.services.subscription_service`](src/subscription_management/logic/services/subscription_service.py)
serves as a running example.
Its `trcks.oop.Wrapper` chain checks the product status
and then creates the subscription in the repository.
The router in
[`subscription_management.logic.routers.subscription_router`](src/subscription_management/logic/routers/subscription_router.py)
maps each domain error to an appropriate HTTP exception.
The following subsections use this flow to illustrate three patterns.

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
can contribute its own domain error.
The generic type parameters of `trcks.oop.Wrapper` track these errors,
so a static type checker infers the exact union instead of falling back to `Any`.
For example, the `_check_that_product_and_user_exist` helper in
[`subscription_management.logic.repositories.subscription_repository`](src/subscription_management/logic/repositories/subscription_repository.py)
reads the product and then the user,
contributing a `ProductWithIdDoesNotExistError`
and a `UserWithIdDoesNotExistError` respectively.
