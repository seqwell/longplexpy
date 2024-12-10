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

# Create a New Release

## Trigger a Version Bump

- Navigate to the [Trigger Version Bump Action](https://github.com/seqwell/longplexpy/actions/workflows/trigger_version_bump.yml).
- Select "Run Workflow" and enter a new version of the form "#.#.#".
Ensure the new version is higher than the current version.
See [Semantic Versioning](https://semver.org/) for help selecting the next version.

## Merge the Versioning PR

- The trigger version bump action will open a new PR with a title similar to "chore(#.#.#): update pyproject version"
- Perform a squash merge on this PR to commit the version bump to main

## Confirm the Release was Created
- Navigate to [Add Version Tag Action](https://github.com/seqwell/longplexpy/actions/workflows/tag_and_release.yml).
- You should see a workflow run with a title similar to the PR title, "chore(#.#.#): update pyproject version"
- Select the action and confirm all four jobs completed successfully.
- If the jobs completed successfully, a new tag matching the "#.#.#" pattern should have been added to main.
You can check the [tags page](https://github.com/seqwell/longplexpy/tags)
- If the jobs completed successfully, there should also be a new release on the [releases page](https://github.com/seqwell/longplexpy/releases).


## Confirm the Docker Image was Build and Deployed
- Navigate to [Build and Deploy Action](https://github.com/seqwell/longplexpy/actions/workflows/build_and_deploy.yml)
- You should see two workflow runs with titles similar to the PR title, "chore(#.#.#): update pyproject version".
One should have a triggering event as the new tag "#.#.#" and one should have a triggering event as `main`.
- A green checkmark on these actions indicates the docker image was built, tagged, and pushed to the [seqwell/longplexpy](https://registry.hub.docker.com/r/seqwell/longplexpy) repo on Dockerhub.
