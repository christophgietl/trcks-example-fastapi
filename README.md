# trcks-example-fastapi

This is an example FastAPI application that demonstrates
how to use the `trcks` library for railway-oriented programming.

## Running the example application

1. Install `uv` if you have not already done so.
2. Clone the `trcks-example-fastapi` repository and `cd` into it.
3. Start the development server by running `uv run fastapi dev`.

## Project structure

The directory [`app/logic/repositories/`](app/logic/repositories/) contains
repository classes with async CRUD methods
that usually return `trcks.Result` values.

The directory [`app/logic/services/`](app/logic/services/) contains
service classes that implement business logic on top of the repository classes.
Their methods usually return `trcks.AwaitableResult` values.

The directory [`app/logic/routers/`](app/logic/routers/) contains
FastAPI routers.
They call and await the service class methods and
pattern-match on the resulting `trcks.Result` values:

1. The payload of `trcks.Success` values is usually returned to the client
   with an appropriate HTTP success status code (e.g., 200, 201, 204).
2. The error of `trcks.Failure` values is mapped to an appropriate
   HTTP exception and raised.
