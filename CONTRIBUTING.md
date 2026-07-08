# Contributing to `trcks-example-fastapi`

Thank you for considering contributing to `trcks-example-fastapi`!
The following section describes how to set up and use a development environment.

## Development environment

`trcks-example-fastapi` uses the following developer tools:

- [import-linter](https://import-linter.readthedocs.io)
  for enforcing rules for the imports within and between Python packages
- [pre-commit](https://pre-commit.com) for managing Git hooks
  (particularly for code formatting and linting)
- [pyright](https://microsoft.github.io/pyright/) for static type checking
- [pytest](https://pytest.org) for unit testing and doctests
- [uv](https://docs.astral.sh/uv/) for dependency management

### Setup

Please follow these steps to set up your development environment:

1. Install `uv` if you have not already done so.
2. Clone the `trcks-example-fastapi` repository and `cd` into it.
3. Install (development) dependencies by running `uv sync`.
   The project uses a `src` layout and the `uv_build` backend, so `uv sync`
   installs the package in editable mode.
4. Set up the Git hooks by executing `uv run pre-commit install`.
   The output should look something like this:

   ```plain
   pre-commit installed at .git/hooks/commit-msg
   pre-commit installed at .git/hooks/pre-commit
   ```

### Usage

Check [the section "Development tools" in `AGENTS.md`](AGENTS.md#development-tools)
for instructions on how to use the development tools.
