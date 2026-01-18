## Docs snippet checks

This directory contains tests that check that the contents of files in the `./docs_snippets/` directory match the expected output. These tests can also be used to regenerate the contents of the snippet files.

Currently, these tests are used to validate user-facing guides in `/docs/docs` that contain a lot of CLI invocations. This lets us ensure that guides do not break when we make changes to the CLI, and allows us to easily regenerate the snippets if we change the output format.

### Prerequisites

Before running tests or regenerating snippets, you will need to create a virtual environment and run `make dev_install` in the root folder of the Dagster repo, then set the `DAGSTER_GIT_REPO_DIR` environment variable.

### Running the tests

To run the tests, invoke the `docs_snapshot_test` tox environment in `examples/docs_snippets`.

```bash
tox -e docs_snapshot_test
```

### Regenerating snippets

To update the snippets, invoke the `docs_snapshot_update` environment:

```bash
tox -e docs_snapshot_update
```

Typically, you will want to only regenerate a subset of the snippets, which is faster:

```bash
tox -e docs_snapshot_update -- docs_snippets_tests/snippet_checks/guides/components/integrations/test_dbt_component.py
```

### Running the commands with make

These commands are aliased in the `/docs` directory, through the Makefile, for convenience - they run all tests and regenerate all snippets, which can take a few minutes.

```bash
# Regenerate CLI snippets
make regenerate_cli_snippets

# Regenerate CLI snippets and immediately run the tests
make regenerate_cli_snippets_and_test
```
