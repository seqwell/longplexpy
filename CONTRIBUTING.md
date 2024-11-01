# Development and Testing

To test the codebase, run the following command:

```console
poetry run pytest
```

The command will:

- Execute unit tests with [`pytest`](https://docs.pytest.org/)
- Test the language typing with [`mypy`](https://mypy-lang.org/)
- Test for linting and styling errors with [`ruff`](https://docs.astral.sh/ruff/)
- Emit a testing coverage report with [`coverage`](https://coverage.readthedocs.io/)

To format the code in the library, run the following commands:

```console
poetry run ruff check --select I --fix
poetry run ruff format longplexpy tests
```

To generate a code coverage report locally, run the following command:

```console
poetry run coverage html
```

# Building the Docker Image

The docker image can be built by running:

```console
ci/docker-build-image
```
