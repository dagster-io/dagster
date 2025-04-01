## Docs Snippet Checks

This directory contains tests which check that the contents of files in the `./docs_snippets/` directory match the expected output.

Currently, this is used to validate user-facing guides which primarily consist of CLI invocations. This lets us ensure that guides do
not break when we make changes to the CLI, and allows us to easily regenerate the snippets if we change the output format.

### Running the tests

To run the tests, invoke the `docs_snapshot_test` tox environment in `examples/docs_snippets`.

```bash
tox -e docs_snapshot_test
```

To update the snippets, instead invoke the `docs_snapshot_update` environment:

```bash
tox -e docs_snapshot_update
```

These commands are aliased in the `/docs` directory, through the Makefile, for convenience:

```bash
# Regenerate CLI snippets
make regenerate_cli_snippets

# Regenerate CLI snippets and immediately run the tests
make regenerate_cli_snippets_and_test
```
