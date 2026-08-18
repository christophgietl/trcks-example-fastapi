# Contributing to `trcks-example-fastapi`

Thank you for considering contributing to `trcks-example-fastapi`!
The following sections describe how to set up your development environment and
list the development tools it provides.

## How-to: Set up your development environment

Please follow these steps to set up your development environment:

1. Install `uv` if you have not already done so.
2. Clone the `trcks-example-fastapi` repository and `cd` into it.
3. Install (development) dependencies by running `uv sync`.
4. Set up the Git hooks by executing `uv run pre-commit install`.
   The output should look something like this:

   ```plain
   pre-commit installed at .git/hooks/commit-msg
   pre-commit installed at .git/hooks/pre-commit
   ```

## Reference: Development tools

`trcks-example-fastapi` uses the following developer tools:

- [import-linter](https://import-linter.readthedocs.io)
  for enforcing rules for the imports within and between Python packages
- [Library Skills](https://library-skills.io) for managing library skills for coding agents.
- [pre-commit](https://pre-commit.com) for managing Git hooks
  (particularly for code formatting and linting)
- [pyright](https://microsoft.github.io/pyright/) for static type checking
- [pytest](https://pytest.org) for testing
- [uv](https://docs.astral.sh/uv/) for dependency management

Check [the section "Development tools" in `AGENTS.md`](AGENTS.md#development-tools)
for instructions on how to use the development tools.
