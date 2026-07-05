# trcks-example-fastapi

`trcks-example-fastapi` is an example FastAPI application.
It demonstrates how to use the `trcks` library for railway-oriented programming.

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

1. The payload of `trcks.Success` values is returned to the client
   with an appropriate HTTP success status code (e.g. 200, 201, and 204).
2. The payload of `trcks.Failure` values is mapped to an appropriate
   HTTP exception and raised.
