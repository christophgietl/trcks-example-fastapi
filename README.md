# trcks-example-fastapi

This repository contains an example FastAPI application.
It demonstrates type-safe railway-oriented programming with
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
[`subscription_management.logic.repositories`](subscription_management/logic/repositories/)
contains repository classes with public CRUD methods.
These methods return `trcks.AwaitableResult` or `trcks.AwaitableTuple` values.

The package
[`subscription_management.logic.services`](subscription_management/logic/services/)
contains service classes that implement business logic on top of the repository
classes.
Their public methods return `trcks.AwaitableResult` or `trcks.AwaitableTuple` values.

The package
[`subscription_management.logic.routers`](subscription_management/logic/routers/)
contains FastAPI routers that call and await the service class methods.
Awaited values of type `trcks.Result` are then handled as follows:
The payload of `trcks.Success` values is returned.
The payload of `trcks.Failure` values is mapped to an appropriate
HTTP exception and raised.
